"""
Tests for the engine/pgx pharmacogenomics subsystem.
"""
from __future__ import annotations

from engine.pgx import Phenotype
from engine.pgx.cpic import (
    apply_phenoconversion,
    generate_recommendations,
)
from engine.pgx.cpic.phenotype import (
    activity_score,
    diplotype_to_phenotype,
    score_to_phenotype,
)
from engine.pgx.hgnn import calibrate_conformal_set, predict_drug_response
from engine.pgx.orchestrator import pgx_stage
from engine.pgx.prs_pgx import calculate_pgx_prs
from engine.pgx.star_alleles.array_caller import call_star_alleles_from_variants
from engine.pgx.star_alleles.hla_caller import call_hla_from_variants


def _v(rsid: str, alt: str, zyg: str = "het", ref: str = "G") -> dict:
    return {"rsid": rsid, "ref": ref, "alt": alt, "genotype": zyg}


# ── Star-allele caller ──────────────────────────────────────────────────────

def test_cyp2c19_homozygous_loss_is_poor_metabolizer():
    variants = [_v("rs4244285", "A", "hom")]
    calls = {c.gene: c for c in call_star_alleles_from_variants(variants)}
    c = calls["CYP2C19"]
    assert c.diplotype == "*2/*2"
    assert c.phenotype == Phenotype.POOR
    assert c.activity_score == 0.0


def test_cyp2c19_no_variants_is_normal_metabolizer():
    calls = {c.gene: c for c in call_star_alleles_from_variants([])}
    c = calls["CYP2C19"]
    assert c.diplotype == "*1/*1"
    assert c.phenotype == Phenotype.NORMAL


def test_cyp2c19_increased_function_is_rapid_or_ultrarapid():
    # *17/*17 → 1.5+1.5 = 3.0
    variants = [_v("rs12248560", "T", "hom")]
    calls = {c.gene: c for c in call_star_alleles_from_variants(variants)}
    c = calls["CYP2C19"]
    assert c.phenotype == Phenotype.ULTRARAPID


def test_cyp2d6_evidence_tier_is_tentative_from_array():
    variants = [_v("rs3892097", "A", "het")]
    calls = {c.gene: c for c in call_star_alleles_from_variants(variants)}
    assert calls["CYP2D6"].evidence_tier == "tentative-no-sv"


def test_tpmt_3b_and_3c_resolves_to_3a():
    variants = [_v("rs1800460", "T", "het"), _v("rs1142345", "C", "het")]
    calls = {c.gene: c for c in call_star_alleles_from_variants(variants)}
    assert calls["TPMT"].diplotype.startswith("*3A")


def test_vkorc1_homozygous_low_score():
    variants = [_v("rs9923231", "T", "hom")]
    calls = {c.gene: c for c in call_star_alleles_from_variants(variants)}
    c = calls["VKORC1"]
    assert c.diplotype == "T/T"
    assert c.activity_score == 1.0


# ── HLA caller ──────────────────────────────────────────────────────────────

def test_hla_b5701_detected_from_tag_snp():
    variants = [_v("rs2395029", "G", "het")]
    calls = {h.locus: h for h in call_hla_from_variants(variants)}
    assert calls["HLA-B*57:01"].present is True
    assert "abacavir" in calls["HLA-B*57:01"].risk_drugs


def test_hla_b1502_absent_when_no_tag_snp():
    calls = {h.locus: h for h in call_hla_from_variants([])}
    assert calls["HLA-B*15:02"].present is False


# ── Phenotype lookup ────────────────────────────────────────────────────────

def test_activity_score_and_diplotype_phenotype():
    assert activity_score("CYP2C19", "*1/*2") == 1.0
    assert diplotype_to_phenotype("CYP2C19", "*1/*2") == Phenotype.INTERMEDIATE
    assert score_to_phenotype("CYP2D6", 0.0) == Phenotype.POOR


# ── Phenoconversion ─────────────────────────────────────────────────────────

def test_phenoconversion_strong_inhibitor_converts_nm_to_pm():
    # CYP2D6 *1/*1 NM (score 2.0) + paroxetine (strong inhibitor) → PM
    starting = call_star_alleles_from_variants([])
    starting = [c for c in starting if c.gene == "CYP2D6"]
    assert starting[0].phenotype == Phenotype.NORMAL
    adjusted, notes = apply_phenoconversion(starting, ["paroxetine"])
    assert adjusted[0].phenotype == Phenotype.POOR
    assert any("paroxetine" in n for n in notes)


def test_phenoconversion_no_meds_returns_unchanged():
    starting = call_star_alleles_from_variants([])
    adjusted, notes = apply_phenoconversion(starting, None)
    assert notes == []


# ── CPIC recommendations ────────────────────────────────────────────────────

def test_cyp2c19_pm_gets_clopidogrel_warning():
    variants = [_v("rs4244285", "A", "hom")]
    star = call_star_alleles_from_variants(variants)
    hla = call_hla_from_variants(variants)
    recs = generate_recommendations(star, hla)
    drugs = {r.drug for r in recs}
    assert "clopidogrel" in drugs
    clop = next(r for r in recs if r.drug == "clopidogrel")
    assert clop.classification == "strong"
    assert clop.gene == "CYP2C19"


def test_hla_present_generates_abacavir_warning():
    variants = [_v("rs2395029", "G", "het")]
    star = call_star_alleles_from_variants(variants)
    hla = call_hla_from_variants(variants)
    recs = generate_recommendations(star, hla)
    abacavir = [r for r in recs if r.drug == "abacavir"]
    assert abacavir and abacavir[0].classification == "strong"


# ── PRS ──────────────────────────────────────────────────────────────────────

def test_clopidogrel_prs_high_when_loss_of_function_homozygous():
    variants = [_v("rs4244285", "A", "hom")]
    prs = {p.trait: p for p in calculate_pgx_prs(variants)}
    assert prs["clopidogrel_htpr"].score > 1.2
    assert prs["clopidogrel_htpr"].risk_tier == "high"


def test_prs_low_when_no_risk_variants():
    variants = [_v("rs4244285", "G", "ref")]   # dosage = 0
    prs = {p.trait: p for p in calculate_pgx_prs(variants)}
    assert prs["clopidogrel_htpr"].risk_tier == "low"


# ── Drug predictions + conformal ────────────────────────────────────────────

def test_drug_predictions_uncalibrated_without_real_calibration():
    """With no real calibration set, no confidence guarantee may be claimed."""
    variants = [_v("rs4244285", "A", "hom"), _v("rs2395029", "G", "het")]
    star = call_star_alleles_from_variants(variants)
    hla = call_hla_from_variants(variants)
    prs = calculate_pgx_prs(variants)
    raw = predict_drug_response(star, hla, prs)
    out = calibrate_conformal_set(raw, confidence=0.9)
    for p in out:
        assert p.confidence_level is None
        assert p.prediction_set == ["uncalibrated"]


def test_drug_predictions_calibrated_with_real_calibration():
    """Given an explicit real calibration set, emit a confidence-bearing set."""
    variants = [_v("rs4244285", "A", "hom"), _v("rs2395029", "G", "het")]
    star = call_star_alleles_from_variants(variants)
    hla = call_hla_from_variants(variants)
    prs = calculate_pgx_prs(variants)
    raw = predict_drug_response(star, hla, prs)
    cal = {
        "respond":     [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50],
        "non_respond": [0.08, 0.13, 0.18, 0.23, 0.28, 0.33, 0.38, 0.43, 0.48, 0.55],
    }
    calibrated = calibrate_conformal_set(
        raw, confidence=0.9, calibration=cal, calibration_is_real=True,
    )
    for p in calibrated:
        assert p.confidence_level == 0.9
        assert p.prediction_set
        assert all(x in {"respond", "non_respond", "indeterminate"} for x in p.prediction_set)


def test_clopidogrel_predicted_non_respond_for_cyp2c19_pm():
    variants = [_v("rs4244285", "A", "hom")]
    star = call_star_alleles_from_variants(variants)
    hla = call_hla_from_variants(variants)
    prs = calculate_pgx_prs(variants)
    raw = predict_drug_response(star, hla, prs, drugs=["clopidogrel"])
    calibrated = calibrate_conformal_set(raw)
    p = calibrated[0]
    # CYP2C19 PM should bias the point score below 0.5 (non-responder)
    assert p.point_score < 0.5
    assert "CYP2C19" in p.contributing_genes


# ── Orchestrator end-to-end ─────────────────────────────────────────────────

def test_pgx_stage_runs_end_to_end_with_array_input():
    variants = [
        _v("rs4244285", "A", "hom"),    # CYP2C19 *2/*2 → PM
        _v("rs2395029", "G", "het"),    # HLA-B*57:01
        _v("rs9923231", "T", "het"),    # VKORC1 G/T
    ]
    profile = pgx_stage(variants, medications=["paroxetine"])
    # CPIC recommendations cover clopidogrel + abacavir
    drugs = {r.drug for r in profile.recommendations}
    assert "clopidogrel" in drugs
    assert "abacavir" in drugs
    # Phenoconversion happened (CYP2D6 NM → PM via paroxetine)
    assert any("paroxetine" in n for n in profile.phenoconversion_notes)
    # HLA call captured
    assert any(h.locus == "HLA-B*57:01" and h.present for h in profile.hla_calls)
    # PRS computed
    assert any(p.trait == "clopidogrel_htpr" for p in profile.prs_results)
    # Drug predictions all carry conformal sets
    assert profile.drug_predictions
    for p in profile.drug_predictions:
        assert p.prediction_set
    # Summary text mentions actionable findings
    assert profile.summary_text and profile.summary_text != "No actionable pharmacogenomic findings."


def test_pgx_stage_no_findings_for_empty_input():
    profile = pgx_stage([])
    # Should still call default *1/*1 for each gene → no recommendations
    assert profile.recommendations == []
    assert all(not h.present for h in profile.hla_calls)


def test_pgx_stage_serializable():
    profile = pgx_stage([_v("rs4244285", "A", "hom")])
    d = profile.to_dict()
    assert "star_alleles" in d and "recommendations" in d
    # JSON-serializability check
    import json
    json.dumps(d)
