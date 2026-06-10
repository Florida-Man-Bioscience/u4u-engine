"""
The priority tier must not read as a clinical classification when it is only a
heuristic signal (no ClinVar backing) — H-02 containment.
"""
from engine.summary import generate_summary


def test_high_tier_without_clinvar_is_marked_heuristic():
    s = generate_summary({
        "tier": "high", "consequence": "stop_gained", "clinvar": None,
        "disease_name": None, "gnomad_af": 0.0, "genes": ["GENEX"],
        "zygosity": "heterozygous",
    })
    assert s.tier_basis == "heuristic_priority"
    assert "not a clinical diagnosis" in s.headline.lower()
    assert "no clinvar" in s.action_hint.lower()


def test_critical_with_clinvar_is_clinical():
    s = generate_summary({
        "tier": "critical", "consequence": "missense_variant",
        "clinvar": "Pathogenic", "disease_name": "Some condition",
        "gnomad_af": 0.0, "genes": ["BRCA1"], "zygosity": "heterozygous",
    })
    assert s.tier_basis == "clinvar"
    assert "known to cause disease" in s.headline.lower()


def test_low_tier_basis_without_clinvar():
    s = generate_summary({
        "tier": "low", "consequence": "synonymous_variant", "clinvar": None,
        "disease_name": None, "gnomad_af": 0.2, "genes": ["GENEY"],
        "zygosity": "heterozygous",
    })
    assert s.tier_basis == "heuristic_priority"
