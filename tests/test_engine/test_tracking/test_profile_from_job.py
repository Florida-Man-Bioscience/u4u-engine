"""
Tests for the genome-upload → tracking-prior bridge.
"""
from __future__ import annotations

import pytest

from engine.tracking.pharmgkb_catalog import (
    EVIDENCE_BASED_CATALOG,
    PEPTIDES_WITH_EVIDENCE,
)
from engine.tracking.profile_from_job import (
    _zygosity_to_genotype,
    build_profile_from_job_results,
    evidence_payload,
)


# ── Catalog sanity ────────────────────────────────────────────────────────


def test_catalog_is_non_empty_and_glp1_only():
    """Right now PharmGKB evidence only covers GLP-1 receptor agonists."""
    assert len(EVIDENCE_BASED_CATALOG) >= 3
    assert PEPTIDES_WITH_EVIDENCE == frozenset(
        {"Semaglutide", "Liraglutide", "Tirzepatide"}
    )


def test_catalog_entries_carry_unique_rsids():
    rsids = [e.rsid for e in EVIDENCE_BASED_CATALOG]
    assert len(rsids) == len(set(rsids)), "catalog must not duplicate an rsid"


def test_every_catalog_entry_has_evidence_citation():
    """Each variant in the catalog must have a PharmGKB level + PMID."""
    for entry in EVIDENCE_BASED_CATALOG:
        cite = evidence_payload(entry.rsid)
        assert cite is not None, f"{entry.rsid} has no evidence citation"
        assert cite["pmid"], f"{entry.rsid} citation missing PMID"
        assert cite["pharmgkb_level"] in {"1A", "1B", "2A", "2B", "3"}


# ── Zygosity mapping ──────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("heterozygous", "het"),
        ("HET", "het"),
        ("homozygous_alt", "hom_alt"),
        ("hom_alt", "hom_alt"),
        ("HOMOZYGOUS-ALT", "hom_alt"),
        ("homozygous_ref", "hom_ref"),
        ("hom_ref", "hom_ref"),
        ("", None),
        (None, None),
        ("missing", None),
    ],
)
def test_zygosity_mapping(raw, expected):
    assert _zygosity_to_genotype(raw) == expected


# ── Builder behaviour ─────────────────────────────────────────────────────


def test_builder_carries_only_matching_alt_allele():
    """If the patient's alt allele doesn't match the catalog's effect
    allele, dosage must be 0 — the PharmGKB evidence applies to a
    specific allele, not just "any variant at that position"."""
    # rs7903146 effect_allele is "T". Patient carries "G" instead.
    results = {"variants": [{"rsid": "rs7903146", "alt": "G", "zygosity": "het"}]}
    profile = build_profile_from_job_results(results, job_id="j1")
    record = next(v for v in profile.variants if v.rsid == "rs7903146")
    assert record.dosage == 0
    assert all(w == 0.0 for w in record.peptide_effects.values())


def test_builder_dosage_scales_effect_weights():
    """A homozygous-alt carrier should get 2x the per-allele weight."""
    results = {
        "variants": [
            {"rsid": "rs7903146", "alt": "T", "zygosity": "homozygous_alt"},
        ]
    }
    profile = build_profile_from_job_results(results, job_id="j1")
    rec = next(v for v in profile.variants if v.rsid == "rs7903146")
    assert rec.dosage == 2
    # rs7903146 is level 2B → per-allele weight = -0.06 → dosage 2 → -0.12
    assert rec.peptide_effects["Semaglutide"] == pytest.approx(-0.12)
    assert rec.peptide_effects["Liraglutide"] == pytest.approx(-0.12)


def test_builder_dense_over_catalog_when_variants_absent():
    """rsIDs the job didn't observe must still appear in the profile as
    hom_ref/dosage=0 so downstream prior accounting is consistent
    across patients."""
    profile = build_profile_from_job_results({"variants": []}, job_id="j1")
    assert len(profile.variants) == len(EVIDENCE_BASED_CATALOG)
    for v in profile.variants:
        assert v.dosage == 0
        assert v.genotype == "hom_ref"


def test_builder_source_carries_job_id():
    profile = build_profile_from_job_results({"variants": []}, job_id="abc123")
    assert profile.source == "job:abc123"


def test_builder_ignores_non_catalog_variants():
    """Variants not in the evidence catalog must not produce profile
    entries — only catalog rsIDs are ever materialised."""
    results = {
        "variants": [
            {"rsid": "rs99999999", "alt": "T", "zygosity": "het"},
            {"rsid": "rs88888888", "alt": "G", "zygosity": "hom_alt"},
        ]
    }
    profile = build_profile_from_job_results(results, job_id="j1")
    rsids_in_profile = {v.rsid for v in profile.variants}
    catalog_rsids = {e.rsid for e in EVIDENCE_BASED_CATALOG}
    assert rsids_in_profile == catalog_rsids
    assert all(v.dosage == 0 for v in profile.variants)


def test_builder_tirzepatide_only_gipr_variant():
    """GIPR rs1800437 should only carry weight for tirzepatide — pure
    GLP-1 agonists (semaglutide, liraglutide) don't engage GIPR."""
    results = {
        "variants": [
            {"rsid": "rs1800437", "alt": "C", "zygosity": "het"},
        ]
    }
    profile = build_profile_from_job_results(results, job_id="j1")
    rec = next(v for v in profile.variants if v.rsid == "rs1800437")
    assert rec.dosage == 1
    assert "Tirzepatide" in rec.peptide_effects
    assert rec.peptide_effects["Tirzepatide"] != 0.0
    # Liraglutide / Semaglutide should NOT have a key here because
    # the catalog entry doesn't reference them at all.
    assert "Semaglutide" not in rec.peptide_effects
    assert "Liraglutide" not in rec.peptide_effects


def test_builder_handles_case_insensitive_alt():
    """Pipeline parsers sometimes emit lowercase alt alleles; the
    matcher must be case-insensitive so we don't reject real carriers."""
    results = {
        "variants": [
            {"rsid": "rs7903146", "alt": "t", "zygosity": "het"},
        ]
    }
    profile = build_profile_from_job_results(results, job_id="j1")
    rec = next(v for v in profile.variants if v.rsid == "rs7903146")
    assert rec.dosage == 1


def test_builder_missing_zygosity_is_zero_dosage():
    """A variant present in the job but with no zygosity field can't be
    assigned a dosage — treat as not carried."""
    results = {
        "variants": [
            {"rsid": "rs7903146", "alt": "T", "zygosity": None},
        ]
    }
    profile = build_profile_from_job_results(results, job_id="j1")
    rec = next(v for v in profile.variants if v.rsid == "rs7903146")
    assert rec.dosage == 0
