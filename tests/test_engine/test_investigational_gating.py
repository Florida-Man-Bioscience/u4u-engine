"""
Tests that investigational (non-FDA-approved) peptides do not carry
patient-facing efficacy claims.
"""
from engine.annotators.peptide_mapper import map_peptide_coverage
from engine.dossier_generator import generate_dossiers


def _variant(gene, clinvar="Pathogenic"):
    return {"genes": [gene], "rsid": "rs1799983", "clinvar": clinvar,
            "consequence": "missense_variant", "variant_id": "rs1799983"}


def test_peptide_recommendations_marked_investigational():
    mapping = map_peptide_coverage([_variant("NOS3")])
    assert mapping["recommendations"]
    for rec in mapping["recommendations"]:
        assert rec["investigational"] is True
        assert rec["efficacy_claim_allowed"] is False
        assert rec["regulatory_status"].startswith("Investigational")
        assert rec["pathway_match_label"]
        assert rec["efficacy_disclaimer"]


def test_dossier_does_not_assert_efficacy_for_investigational():
    mapping = map_peptide_coverage([_variant("NOS3")])
    result = {"peptide_recommendations": mapping, "variants": [_variant("NOS3")]}
    dossiers = generate_dossiers(result)
    assert dossiers
    for html in dossiers.values():
        assert "Predicted Efficacy" not in html
        assert "Genetic Pathway Analysis" in html
        assert "not FDA-approved" in html
