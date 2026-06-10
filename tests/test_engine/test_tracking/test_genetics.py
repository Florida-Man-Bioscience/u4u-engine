import random

from engine.tracking.genetics import (
    VARIANT_CATALOG,
    GeneticProfile,
    derive_prior,
    derive_responder_prior,
    generate_synthetic_profile,
    responder_strength_from_profile,
)


def test_synthetic_profile_covers_full_catalog():
    profile = generate_synthetic_profile(random.Random(0))
    assert len(profile.variants) == len(VARIANT_CATALOG)
    assert all(v.genotype in {"hom_ref", "het", "hom_alt"} for v in profile.variants)
    assert all(0 <= v.dosage <= 2 for v in profile.variants)


def test_profile_serialisation_roundtrip():
    profile = generate_synthetic_profile(random.Random(7))
    raw = profile.to_json()
    restored = GeneticProfile.from_json(raw)
    assert len(restored.variants) == len(profile.variants)
    assert restored.variants[0].rsid == profile.variants[0].rsid
    assert restored.variants[0].peptide_effects == profile.variants[0].peptide_effects


def test_generate_is_deterministic_under_same_seed():
    a = generate_synthetic_profile(random.Random(42))
    b = generate_synthetic_profile(random.Random(42))
    assert [v.genotype for v in a.variants] == [v.genotype for v in b.variants]


def test_responder_prior_centered_near_one_and_bounded():
    """r = 1 + R_DELTA_SCALE·tanh(w) stays in [1 - R_DELTA_SCALE, 1 + R_DELTA_SCALE]."""
    rng = random.Random(0)
    for _ in range(50):
        profile = generate_synthetic_profile(rng)
        for peptide in ["BPC-157", "CJC-1295", "MOTS-c", "GHK-Cu", "AOD-9604"]:
            r = derive_responder_prior(profile, peptide)
            assert 0.25 <= r.mean <= 1.75
            assert r.sd > 0


def test_biomarker_prior_scales_with_panel_effect():
    """Prior μ on % change should be roughly r × expected_pct."""
    profile = generate_synthetic_profile(random.Random(0))
    # CJC-1295 has IGF-1 (+0.55) and HbA1c (-0.05) as documented effects.
    igf = derive_prior(
        profile, "CJC-1295", expected_pct=0.55, biomarker_name="Serum IGF-1",
    )
    hba = derive_prior(
        profile, "CJC-1295", expected_pct=-0.05, biomarker_name="HbA1c",
    )
    # Same responder strength → IGF prior should be ~11× the magnitude of HbA1c.
    assert abs(igf.mean_pct_change) > abs(hba.mean_pct_change) * 5
    # Sign follows the panel direction (negative for HbA1c).
    assert (igf.mean_pct_change > 0) == (igf.expected_pct_panel > 0)
    assert (hba.mean_pct_change < 0) == (hba.expected_pct_panel < 0)


def test_more_relevant_variants_yields_tighter_responder_prior():
    """A peptide with more catalog hits should yield a tighter r prior."""
    profile = generate_synthetic_profile(random.Random(1))
    cjc = derive_responder_prior(profile, "CJC-1295")
    kiss = derive_responder_prior(profile, "Kisspeptin")
    if cjc.n_relevant_variants > kiss.n_relevant_variants:
        assert cjc.sd <= kiss.sd


def test_responder_strength_centered_near_one():
    """Averaged across many synthetic profiles, responder strength should
    sit near 1.0 (population average)."""
    rng = random.Random(0)
    samples: list[float] = []
    for _ in range(200):
        profile = generate_synthetic_profile(rng)
        samples.append(responder_strength_from_profile(profile, "CJC-1295"))
    mean = sum(samples) / len(samples)
    assert 0.7 < mean < 1.3
