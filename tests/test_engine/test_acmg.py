"""
Tests for the ACMG/AMP evidence-combining rules and the evidence classifier.
"""
from engine.acmg import (
    AcmgConfig, Classification, EvidenceCode, Strength, classify_acmg, combine,
    load_lof_mechanism_genes, load_known_pathogenic_aa,
)


def _p(strength):  # pathogenic code at a given strength
    return EvidenceCode("X", strength, "test")


def _b(strength):
    return EvidenceCode("X", strength, "test")


# ── Combining rules ─────────────────────────────────────────────────────────

def test_pathogenic_pvs1_plus_strong():
    codes = [_p(Strength.VERY_STRONG), _p(Strength.STRONG)]
    assert combine(codes) == Classification.PATHOGENIC


def test_pathogenic_two_strong():
    assert combine([_p(Strength.STRONG), _p(Strength.STRONG)]) == Classification.PATHOGENIC


def test_likely_pathogenic_pvs1_plus_pm():
    codes = [_p(Strength.VERY_STRONG), _p(Strength.MODERATE)]
    assert combine(codes) == Classification.LIKELY_PATHOGENIC


def test_likely_pathogenic_three_moderate():
    codes = [_p(Strength.MODERATE)] * 3
    assert combine(codes) == Classification.LIKELY_PATHOGENIC


def test_benign_standalone():
    assert combine([_b(Strength.STAND_ALONE)]) == Classification.BENIGN


def test_benign_two_strong():
    assert combine([_b(Strength.BENIGN_STRONG), _b(Strength.BENIGN_STRONG)]) == Classification.BENIGN


def test_likely_benign_two_supporting():
    codes = [_b(Strength.BENIGN_SUPPORTING), _b(Strength.BENIGN_SUPPORTING)]
    assert combine(codes) == Classification.LIKELY_BENIGN


def test_contradictory_is_vus():
    # PVS1+PS (pathogenic) AND BA1 (benign) → conflict → VUS
    codes = [_p(Strength.VERY_STRONG), _p(Strength.STRONG), _b(Strength.STAND_ALONE)]
    assert combine(codes) == Classification.UNCERTAIN


def test_insufficient_is_vus():
    assert combine([_p(Strength.SUPPORTING)]) == Classification.UNCERTAIN
    assert combine([]) == Classification.UNCERTAIN


# ── Classifier (evidence assignment) ────────────────────────────────────────

def test_common_variant_is_benign_ba1():
    v = {"genes": ["X"], "consequence": "missense_variant", "gnomad_popmax": 0.2}
    out = classify_acmg(v)
    assert out["classification"] == "Benign"
    assert any(c["code"] == "BA1" for c in out["applied_codes"])
    assert out["requires_human_review"] is True


def test_null_variant_pvs1_only_counted_with_lof_gene():
    # absent in gnomAD (PM2_supporting) + in-silico deleterious (PP3)
    v = {"genes": ["BRCA1"], "consequence": "stop_gained", "gnomad_af": 0.0,
         "insilico_pred": "deleterious"}
    # Without a LoF gene set, PVS1 is a candidate (not counted) → not pathogenic
    out = classify_acmg(v)
    assert all(c["code"] != "PVS1" for c in out["applied_codes"])
    assert any(c["code"] == "PVS1" for c in out["candidate_codes"])
    assert out["classification"] == "Uncertain significance"

    # With BRCA1 in the LoF set: PVS1 (very strong) + 2 supporting (PM2, PP3)
    # → Pathogenic per the 2015 combining rules.
    cfg = AcmgConfig(lof_mechanism_genes=frozenset({"BRCA1"}))
    out2 = classify_acmg(v, cfg)
    assert any(c["code"] == "PVS1" for c in out2["applied_codes"])
    assert out2["classification"] == "Pathogenic"


def test_pm2_not_applied_without_frequency_data():
    v = {"genes": ["X"], "consequence": "missense_variant", "gnomad_af": None}
    out = classify_acmg(v)
    assert all(c["code"] != "PM2_Supporting" for c in out["applied_codes"])
    assert any(c["code"] == "PM2_Supporting" for c in out["candidate_codes"])


def test_clinvar_not_used_as_code_but_reported():
    v = {"genes": ["X"], "consequence": "missense_variant", "gnomad_af": 0.3,
         "clinvar_raw": "Pathogenic"}
    out = classify_acmg(v)
    assert out["clinvar_comparison"] == "Pathogenic"
    assert all("PP5" not in c["code"] and "BP6" not in c["code"] for c in out["applied_codes"])


# ── Curated LoF gene list ───────────────────────────────────────────────────

def test_lof_gene_list_loads_and_contains_known_genes():
    genes = load_lof_mechanism_genes()
    assert genes
    assert "BRCA1" in genes and "MLH1" in genes


def test_pvs1_counted_for_curated_lof_gene_via_default_loader():
    cfg = AcmgConfig(lof_mechanism_genes=load_lof_mechanism_genes())
    v = {"genes": ["BRCA2"], "consequence": "frameshift_variant", "gnomad_af": 0.0,
         "sift_pred": "deleterious", "polyphen_pred": "probably_damaging"}
    out = classify_acmg(v, cfg)
    assert any(c["code"] == "PVS1" for c in out["applied_codes"])


# ── SIFT / PolyPhen → PP3 / BP4 ─────────────────────────────────────────────

def test_concordant_sift_polyphen_deleterious_gives_pp3():
    v = {"genes": ["X"], "consequence": "missense_variant", "gnomad_af": 0.0,
         "sift_pred": "deleterious", "polyphen_pred": "probably_damaging"}
    out = classify_acmg(v)
    assert any(c["code"] == "PP3" for c in out["applied_codes"])


def test_concordant_sift_polyphen_benign_gives_bp4():
    v = {"genes": ["X"], "consequence": "missense_variant", "gnomad_af": 0.0,
         "sift_pred": "tolerated", "polyphen_pred": "benign"}
    out = classify_acmg(v)
    assert any(c["code"] == "BP4" for c in out["applied_codes"])


def test_discordant_sift_polyphen_gives_neither():
    v = {"genes": ["X"], "consequence": "missense_variant", "gnomad_af": 0.0,
         "sift_pred": "deleterious", "polyphen_pred": "benign"}
    out = classify_acmg(v)
    assert all(c["code"] not in ("PP3", "BP4") for c in out["applied_codes"])


# ── PS1 / PM5 (codon-level, reference-gated) ────────────────────────────────

_KNOWN = {("BRCA1", 1699): {"W", "Q"}}


def test_ps1_same_aa_change():
    v = {"genes": ["BRCA1"], "consequence": "missense_variant", "gnomad_af": 0.0,
         "protein_pos": 1699, "alt_aa": "W"}
    out = classify_acmg(v, AcmgConfig(known_pathogenic_aa=_KNOWN))
    assert any(c["code"] == "PS1" for c in out["applied_codes"])


def test_pm5_different_aa_change_same_residue():
    v = {"genes": ["BRCA1"], "consequence": "missense_variant", "gnomad_af": 0.0,
         "protein_pos": 1699, "alt_aa": "R"}  # different alt at a known residue
    out = classify_acmg(v, AcmgConfig(known_pathogenic_aa=_KNOWN))
    codes = [c["code"] for c in out["applied_codes"]]
    assert "PM5" in codes and "PS1" not in codes


def test_no_ps1_pm5_without_reference():
    v = {"genes": ["BRCA1"], "consequence": "missense_variant", "gnomad_af": 0.0,
         "protein_pos": 1699, "alt_aa": "W"}
    out = classify_acmg(v)  # default config: no reference
    assert all(c["code"] not in ("PS1", "PM5") for c in out["applied_codes"])


def test_known_aa_loader_parses_tsv(tmp_path):
    f = tmp_path / "known.tsv"
    f.write_text("# comment\nBRCA1\t1699\tW\nbrca1,1699,Q\nbad row\n", encoding="utf-8")
    ref = load_known_pathogenic_aa(str(f))
    assert ref[("BRCA1", 1699)] == {"W", "Q"}


def test_known_aa_loader_empty_when_file_has_no_rows():
    # The shipped data file is intentionally comment-only → empty reference.
    assert load_known_pathogenic_aa() == {}
