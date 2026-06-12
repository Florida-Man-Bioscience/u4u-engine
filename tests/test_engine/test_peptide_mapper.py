"""
Unit tests for engine/annotators/peptide_mapper.py

Tests verify peptide gene mapping data integrity, coverage calculation,
and summary generation.
"""

import pytest

from engine.annotators.peptide_mapper import (
    map_peptide_coverage,
    generate_peptide_summary,
    PEPTIDE_GENE_MAP,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_variant(genes, rsid=None, consequence="missense_variant"):
    """Create a minimal annotated variant dict."""
    return {
        "genes": genes if isinstance(genes, list) else [genes],
        "rsid": rsid,
        "consequence": consequence,
        "chrom": "1",
        "pos": 100,
        "ref": "A",
        "alt": "T",
        "zygosity": "heterozygous",
        "score": 50,
    }


# ---------------------------------------------------------------------------
# PEPTIDE_GENE_MAP data integrity
# ---------------------------------------------------------------------------

class TestPeptideGeneMapData:

    def test_has_fourteen_peptides(self):
        assert len(PEPTIDE_GENE_MAP) == 14

    def test_all_peptides_have_required_fields(self):
        for key, entry in PEPTIDE_GENE_MAP.items():
            assert "genes" in entry, f"{key} missing 'genes'"
            assert "rationale" in entry, f"{key} missing 'rationale'"
            assert "refs" in entry, f"{key} missing 'refs'"
            assert "category" in entry, f"{key} missing 'category'"
            assert "category_display" in entry, f"{key} missing 'category_display'"

    def test_all_peptides_have_nonempty_genes(self):
        for key, entry in PEPTIDE_GENE_MAP.items():
            assert len(entry["genes"]) > 0, f"{key} has empty gene set"

    def test_known_peptides_present(self):
        expected = [
            "GHK-Cu + BPC-157 + TB-500",
            "CJC-1295 + Ipamorelin",
            "BPC-157 + TB-500",
            "AOD-9604",
            "MOTS-c",
            "Epithalon",
            "Thymosin Alpha-1",
            "Matrixyl",
            "Argireline",
            "SNAP-8",
            "Semaglutide",
            "Tirzepatide",
            "Liraglutide",
        ]
        for name in expected:
            assert name in PEPTIDE_GENE_MAP, f"Missing peptide: {name}"


# ---------------------------------------------------------------------------
# map_peptide_coverage — basic behavior
# ---------------------------------------------------------------------------

class TestMapPeptideCoverage:

    def test_empty_variants_returns_all_peptides_uncovered(self):
        result = map_peptide_coverage([])
        assert len(result["recommendations"]) == 14
        assert result["peptides_with_coverage"] == 0
        for rec in result["recommendations"]:
            assert rec["coverage"] == 0
            assert rec["genes_found"] == []

    def test_irrelevant_genes_zero_coverage(self):
        variants = [_make_variant("BRCA1"), _make_variant("TP53")]
        result = map_peptide_coverage(variants)
        assert result["peptides_with_coverage"] == 0

    def test_col1a1_hit_covers_multiple_peptides(self):
        """COL1A1 appears in both GHK-Cu combo and Matrixyl."""
        variants = [_make_variant("COL1A1")]
        result = map_peptide_coverage(variants)

        covered_names = [
            r["peptide_name"] for r in result["recommendations"]
            if r["coverage"] > 0
        ]
        assert "GHK-Cu + BPC-157 + TB-500" in covered_names
        assert "Matrixyl" in covered_names
        assert result["peptides_with_coverage"] >= 2

    def test_full_coverage_for_single_gene_peptide(self):
        """AOD-9604 needs only ADRB3."""
        variants = [_make_variant("ADRB3")]
        result = map_peptide_coverage(variants)

        aod = next(
            r for r in result["recommendations"]
            if r["peptide_name"] == "AOD-9604"
        )
        assert aod["coverage"] == 1.0
        assert aod["genes_found"] == ["ADRB3"]
        assert aod["genes_missing"] == []

    def test_partial_coverage(self):
        """GHK-Cu + BPC-157 + TB-500 needs COL1A1, COL1A2, SMYD3."""
        variants = [_make_variant("COL1A1")]  # 1 of 3
        result = map_peptide_coverage(variants)

        ghk = next(
            r for r in result["recommendations"]
            if r["peptide_name"] == "GHK-Cu + BPC-157 + TB-500"
        )
        assert ghk["coverage"] == round(1 / 3, 2)
        assert "COL1A1" in ghk["genes_found"]
        assert len(ghk["genes_missing"]) == 2

    def test_nos3_covers_bpc157_tb500(self):
        variants = [_make_variant("NOS3")]
        result = map_peptide_coverage(variants)

        bpc = next(
            r for r in result["recommendations"]
            if r["peptide_name"] == "BPC-157 + TB-500"
        )
        assert bpc["coverage"] == 1.0

    def test_glp1r_covers_glp1_agonists(self):
        """GLP1R variant should surface the GLP-1 agonist peptides."""
        variants = [_make_variant("GLP1R", rsid="rs10305420")]
        result = map_peptide_coverage(variants)

        covered = {
            r["peptide_name"] for r in result["recommendations"]
            if r["coverage"] > 0
        }
        assert {"Semaglutide", "Tirzepatide", "Liraglutide"}.issubset(covered)

    def test_tirzepatide_full_coverage_requires_three_genes(self):
        """Tirzepatide needs GLP1R, GIPR, and TCF7L2 for full coverage."""
        variants = [
            _make_variant("GLP1R"),
            _make_variant("GIPR"),
            _make_variant("TCF7L2"),
        ]
        result = map_peptide_coverage(variants)
        tirz = next(
            r for r in result["recommendations"]
            if r["peptide_name"] == "Tirzepatide"
        )
        assert tirz["coverage"] == 1.0
        assert tirz["category"] == "glp1"

    def test_case_insensitive_gene_matching(self):
        """Gene matching should be case-insensitive."""
        variants = [_make_variant("adrb3")]  # lowercase
        result = map_peptide_coverage(variants)

        aod = next(
            r for r in result["recommendations"]
            if r["peptide_name"] == "AOD-9604"
        )
        assert aod["coverage"] == 1.0

    def test_result_has_all_required_keys(self):
        result = map_peptide_coverage([_make_variant("NOS3")])
        assert "recommendations" in result
        assert "summary_text" in result
        assert "genes_found_total" in result
        assert "peptides_with_coverage" in result

    def test_recommendation_has_all_required_keys(self):
        result = map_peptide_coverage([_make_variant("NOS3")])
        for rec in result["recommendations"]:
            for key in [
                "peptide_name", "genes_for_genotyping", "genes_found",
                "genes_missing", "coverage", "rationale", "references",
                "category", "category_display",
            ]:
                assert key in rec, f"Missing key: {key}"

    def test_genes_as_string_not_list(self):
        """Some variants may have genes as a string instead of list."""
        variant = {
            "genes": "NOS3",
            "rsid": None,
            "consequence": "missense_variant",
            "score": 10,
        }
        result = map_peptide_coverage([variant])
        assert result["peptides_with_coverage"] > 0


# ---------------------------------------------------------------------------
# generate_peptide_summary
# ---------------------------------------------------------------------------

class TestGeneratePeptideSummary:

    def test_empty_returns_message(self):
        text = generate_peptide_summary([])
        assert "No peptide" in text
        assert len(text) > 0

    def test_summary_from_full_mapping(self):
        result = map_peptide_coverage([_make_variant("ADRB3")])
        assert len(result["summary_text"]) > 0

    def test_no_variants_summary(self):
        result = map_peptide_coverage([])
        assert "baseline" in result["summary_text"].lower() or "no" in result["summary_text"].lower()

    def test_with_variants_summary(self):
        result = map_peptide_coverage([_make_variant("NOS3"), _make_variant("COL1A1")])
        assert len(result["summary_text"]) > 20
