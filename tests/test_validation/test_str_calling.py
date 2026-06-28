"""
Tests for the Tier A AR CAG STR-calling validation track.

Offline — no ExpansionHunter binary, no BAM. Exercises the parser against
synthetic EH output and the interpretation classifier across its breakpoints.
"""
from __future__ import annotations

from validation.tier_a.str_calling import (
    BOUNDARY_CASES,
    run_interpretation_verification,
    run_parser_concordance,
    run_str_validation,
)


def test_parser_concordance_all_match():
    report = run_parser_concordance()
    conc = report["concordance"]
    assert conc["n_compared"] == len(report["details"])
    assert conc["concordance_rate"] == 1.0, [
        d for d in report["details"] if not d["ok"]
    ]


def test_parser_takes_shorter_diploid_allele():
    report = run_parser_concordance()
    by_id = {d["id"]: d for d in report["details"]}
    # REPCN=19/22 with no JSON RepeatSize → min allele 19
    assert by_id["vcf_diploid_min_19"]["parsed"] == 19


def test_parser_json_overrides_vcf():
    report = run_parser_concordance()
    by_id = {d["id"]: d for d in report["details"]}
    # VCF says 30/30 but JSON RepeatSize=22 is authoritative
    assert by_id["json_overrides_vcf"]["parsed"] == 22


def test_interpretation_boundaries_exact():
    report = run_interpretation_verification()
    conc = report["concordance"]
    assert conc["concordance_rate"] == 1.0, [
        d for d in report["details"] if not d["ok"]
    ]


def test_interpretation_covers_every_tier():
    levels = {exp for _, exp in BOUNDARY_CASES}
    assert levels == {
        "VERY_HIGH", "HIGH", "NORMAL", "REDUCED", "LOW", "VERY_LOW_PATHOLOGIC",
    }


def test_kennedy_disease_threshold_is_36():
    """Boundary guard: 35 is LOW, 36 crosses into pathologic (SBMA range)."""
    report = run_interpretation_verification()
    by_count = {d["repeat_count"]: d for d in report["details"]}
    assert by_count[35]["actual_level"] == "LOW"
    assert by_count[36]["actual_level"] == "VERY_LOW_PATHOLOGIC"


def test_full_report_structure_and_env():
    report = run_str_validation()
    assert report["track"] == "ar_cag_str_calling"
    env = report["environment"]
    # In CI the binary/reference are absent; the field must say so honestly.
    assert "end_to_end_runnable" in env
    assert isinstance(env["end_to_end_runnable"], bool)
