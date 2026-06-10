"""Tests for the result-level ACMG aggregation (summarize_acmg)."""
from engine.acmg import summarize_acmg


def _v(vid, classification, clinvar):
    return {"variant_id": vid, "acmg": {"classification": classification,
                                        "clinvar_comparison": clinvar}}


def test_counts_by_classification():
    variants = [
        _v("a", "Pathogenic", "Pathogenic"),
        _v("b", "Benign", "Benign"),
        _v("c", "Uncertain significance", None),
    ]
    out = summarize_acmg(variants)
    assert out["counts"]["Pathogenic"] == 1
    assert out["variants_classified"] == 3
    assert out["requires_review"] == 3


def test_opposing_discordance_flagged():
    variants = [_v("x", "Benign", "Pathogenic")]
    out = summarize_acmg(variants)
    d = out["clinvar_discordances"]
    assert len(d) == 1 and d[0]["severity"] == "opposing"
    assert d[0]["variant_id"] == "x"


def test_clinvar_only_discordance():
    variants = [_v("y", "Uncertain significance", "Pathogenic")]
    out = summarize_acmg(variants)
    assert out["clinvar_discordances"][0]["severity"] == "clinvar_only"


def test_acmg_only_discordance():
    variants = [_v("z", "Likely pathogenic", None)]
    out = summarize_acmg(variants)
    assert out["clinvar_discordances"][0]["severity"] == "acmg_only"


def test_concordant_not_flagged():
    variants = [_v("c1", "Pathogenic", "Pathogenic"),
                _v("c2", "Benign", "Likely benign")]
    out = summarize_acmg(variants)
    assert out["clinvar_discordances"] == []


def test_variants_without_acmg_ignored():
    out = summarize_acmg([{"variant_id": "n"}])
    assert out["variants_classified"] == 0
