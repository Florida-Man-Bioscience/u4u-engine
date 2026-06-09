import random

from engine.tracking.genetics import (
    VARIANT_CATALOG,
    GeneticProfile,
    derive_prior,
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


def test_prior_mean_within_bounded_range():
    """PRIOR_SCALE * tanh(w) → |mean| ≤ PRIOR_SCALE no matter how extreme."""
    rng = random.Random(0)
    for _ in range(50):
        profile = generate_synthetic_profile(rng)
        for peptide in ["BPC-157", "CJC-1295", "MOTS-c", "GHK-Cu", "AOD-9604"]:
            prior = derive_prior(profile, peptide)
            assert -0.4 < prior.mean_pct_change < 0.4
            assert prior.sd_pct_change > 0


def test_more_relevant_variants_yields_tighter_prior():
    """A prior built from a peptide with many catalog hits should be at
    least as tight as one with fewer hits."""
    profile = generate_synthetic_profile(random.Random(1))
    # CJC-1295 has ~4 catalog entries with non-zero weights; Kisspeptin has 1.
    cjc = derive_prior(profile, "CJC-1295")
    kiss = derive_prior(profile, "Kisspeptin")
    if cjc.n_relevant_variants > kiss.n_relevant_variants:
        assert cjc.sd_pct_change <= kiss.sd_pct_change


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
