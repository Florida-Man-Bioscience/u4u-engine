"""
Tests for the Tier A genome-build handling validation track.

Runs entirely offline — `engine.genome_build` is pure header parsing. Verifies
both that the validation harness reports correctly AND, via the harness, that
the H-01 control in the engine actually holds on the fixture matrix.
"""
from __future__ import annotations

from validation.tier_a.build_handling import (
    FIXTURES,
    BuildFixture,
    _vcf,
    run_build_validation,
)


def test_all_fixtures_detect_expected_build():
    report = run_build_validation()
    det = report["build_detection"]
    # every fixture's build should be detected concordantly
    assert det["n_compared"] == report["n_fixtures"]
    assert det["concordance_rate"] == 1.0, det["discordances"]


def test_all_gating_actions_correct():
    report = run_build_validation()
    gate = report["gating"]
    assert gate["n_correct"] == gate["n_total"], [
        r for r in gate["results"] if not r["action_correct"]
    ]


def test_h01_control_holds_on_fixture_matrix():
    """The headline safety assertion: no non-GRCh38 coordinate file proceeds."""
    report = run_build_validation()
    assert report["safety"]["n_unsafe_passes"] == 0
    assert report["safety"]["h01_control_holds"] is True


def test_grch37_vcf_rejected_without_liftover():
    report = run_build_validation()
    by_id = {r["id"]: r for r in report["gating"]["results"]}
    assert by_id["vcf_grch37_contig"]["actual_action"] == "reject"


def test_grch37_vcf_lifted_when_liftover_available():
    report = run_build_validation()
    by_id = {r["id"]: r for r in report["gating"]["results"]}
    assert by_id["vcf_grch37_liftover"]["actual_action"] == "liftover"


def test_23andme_grch37_proceeds_build_recorded():
    # rsID-resolved formats are never blocked even on GRCh37
    report = run_build_validation()
    by_id = {r["id"]: r for r in report["gating"]["results"]}
    row = by_id["txt_grch37_23andme"]
    assert row["detected_build"] == "GRCh37"
    assert row["actual_action"] == "proceed"


def test_harness_detects_an_injected_unsafe_pass():
    """Guard the guard: if the gate ever let a GRCh37 VCF proceed, the harness
    must flag it as an unsafe pass — proving the safety metric isn't vacuous."""
    # A fixture that LIES about the correct action is irrelevant here; instead we
    # simulate a broken gate by mislabeling a GRCh37 VCF's expected action and
    # confirming the *safety* check (which ignores expected_action) still fires
    # only on real proceed-on-non-GRCh38. So we craft a case the real gate would
    # reject and verify it is NOT flagged, then a hypothetical proceed IS.
    from validation.tier_a import build_handling as bh

    # Real gate rejects GRCh37 VCF → not an unsafe pass.
    safe = run_build_validation([
        BuildFixture("g37", "x.vcf", _vcf(contig_len=249250621),
                     "GRCh37", "reject"),
    ])
    assert safe["safety"]["n_unsafe_passes"] == 0

    # Monkeypatch the planner to wrongly proceed, proving the detector of unsafe
    # passes is live.
    import engine.genome_build as gb
    orig = bh.plan_build_handling
    try:
        bh.plan_build_handling = lambda det, fn, liftover_available=False: {
            "action": "proceed", "detection": det
        }
        broken = run_build_validation([
            BuildFixture("g37", "x.vcf", _vcf(contig_len=249250621),
                         "GRCh37", "reject"),
        ])
        assert broken["safety"]["n_unsafe_passes"] == 1
        assert broken["safety"]["h01_control_holds"] is False
    finally:
        bh.plan_build_handling = orig
