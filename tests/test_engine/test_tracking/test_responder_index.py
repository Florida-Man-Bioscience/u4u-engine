"""
Backward-compat golden test for the Hierarchical Bayesian Responder Index.

The HBRI generalises the scalar responder ``r`` into a multi-feature index η.
With only the genetics adapter registered (the default), the index MUST
reproduce the pre-refactor ``derive_responder_prior`` / ``derive_prior``
numbers exactly. The GOLDEN_* constants below were captured from the current
implementation BEFORE the refactor (see PR description) and are frozen here so
any behaviour drift fails loudly.
"""
from __future__ import annotations

import math
import random

import pytest

from engine.tracking.genetics import (
    R_BASE_SD,
    R_DELTA_SCALE,
    R_MIN_SD,
    derive_prior,
    derive_responder_prior,
    generate_synthetic_profile,
)
from engine.tracking.responder_index import (
    ResponderContext,
    _deta_dlinear,
    registered_adapters,
    responder_index,
)

# (seed, peptide) -> (responder mean, responder sd), captured pre-refactor.
GOLDEN_RESPONDER: dict[tuple[int, str], tuple[float, float]] = {
    (0, "CJC-1295"): (1.2611493766561968, 0.12727922061357855),
    (0, "MOTS-c"): (1.1142269230941992, 0.14696938456699069),
    (0, "BPC-157"): (1.2978239983747373, 0.10392304845413264),
    (7, "CJC-1295"): (1.439687319628128, 0.11384199576606165),
    (7, "MOTS-c"): (1.332724353227207, 0.11384199576606165),
    (7, "BPC-157"): (1.5358793445005228, 0.07675225788801975),
    (42, "CJC-1295"): (1.425893964710908, 0.11384199576606165),
    (42, "MOTS-c"): (0.9425225662399854, 0.10392304845413264),
    (42, "BPC-157"): (1.59576515992588, 0.08485281374238571),
}

# (seed, peptide, expected_pct, biomarker) -> (mean_pct_change, sd_pct_change).
GOLDEN_PRIOR: dict[tuple, tuple[float, float]] = {
    (0, "CJC-1295", 0.55, "Serum IGF-1"): (0.6936321571609083, 0.10819773565098302),
    (7, "CJC-1295", 0.55, "Serum IGF-1"): (0.7918280257954704, 0.10356954185473642),
    (42, "CJC-1295", 0.55, "Serum IGF-1"): (0.7842416805909994, 0.10356954185473642),
}

_ATOL = 1e-12


def test_genetics_adapter_is_registered():
    adapters = registered_adapters()
    assert "genetics" in adapters
    assert adapters["genetics"].peptide_mask("CJC-1295") is True


def test_responder_index_reproduces_legacy_responder_numbers():
    """η, Var(η) genetics-only == legacy derive_responder_prior mean, sd²."""
    for (seed, pep), (gmean, gsd) in GOLDEN_RESPONDER.items():
        profile = generate_synthetic_profile(random.Random(seed))
        idx = responder_index(
            ResponderContext(profile=profile, peptide_name=pep)
        )
        assert math.isclose(idx.eta, gmean, rel_tol=0, abs_tol=_ATOL), (seed, pep)
        assert math.isclose(idx.sd, gsd, rel_tol=0, abs_tol=_ATOL), (seed, pep)
        # var_eta is the square of the legacy responder sd.
        assert math.isclose(idx.var_eta, gsd * gsd, rel_tol=0, abs_tol=_ATOL)


def test_derive_responder_prior_matches_golden():
    for (seed, pep), (gmean, gsd) in GOLDEN_RESPONDER.items():
        profile = generate_synthetic_profile(random.Random(seed))
        r = derive_responder_prior(profile, pep)
        assert math.isclose(r.mean, gmean, rel_tol=0, abs_tol=_ATOL), (seed, pep)
        assert math.isclose(r.sd, gsd, rel_tol=0, abs_tol=_ATOL), (seed, pep)


def test_derive_prior_matches_golden():
    for (seed, pep, exp, bm), (gmean, gsd) in GOLDEN_PRIOR.items():
        profile = generate_synthetic_profile(random.Random(seed))
        gp = derive_prior(profile, pep, expected_pct=exp, biomarker_name=bm)
        assert math.isclose(gp.mean_pct_change, gmean, rel_tol=0, abs_tol=_ATOL)
        assert math.isclose(gp.sd_pct_change, gsd, rel_tol=0, abs_tol=_ATOL)


def test_eta_matches_closed_form():
    """η == 1 + Δ·tanh(w) with genetics only (β_g = 1, linear = w)."""
    profile = generate_synthetic_profile(random.Random(3))
    for pep in ("CJC-1295", "BPC-157", "MOTS-c", "GHK-Cu"):
        idx = responder_index(ResponderContext(profile=profile, peptide_name=pep))
        w = idx.linear  # genetics-only: βᵀx == w
        assert math.isclose(idx.eta, 1.0 + R_DELTA_SCALE * math.tanh(w), abs_tol=_ATOL)


def test_eta_is_bounded():
    """η stays in [1 - Δ, 1 + Δ] regardless of feature magnitude."""
    profile = generate_synthetic_profile(random.Random(11))
    for pep in ("CJC-1295", "BPC-157", "MOTS-c", "GHK-Cu", "Kisspeptin"):
        idx = responder_index(ResponderContext(profile=profile, peptide_name=pep))
        assert 1.0 - R_DELTA_SCALE - 1e-9 <= idx.eta <= 1.0 + R_DELTA_SCALE + 1e-9


def test_var_eta_reproduces_today_sd_contribution():
    """The genetics feature's back-out variance closes the delta-method loop:
    Var(η) == today_sd² for the genetics-only operating point."""
    profile = generate_synthetic_profile(random.Random(5))
    for pep in ("CJC-1295", "BPC-157", "MOTS-c"):
        summary = profile.peptide_effect_summary(pep)
        n = summary["n_relevant_variants"]
        today_sd = max(R_MIN_SD, R_BASE_SD / math.sqrt(1 + 0.5 * n))
        idx = responder_index(ResponderContext(profile=profile, peptide_name=pep))
        assert math.isclose(idx.sd, today_sd, rel_tol=0, abs_tol=_ATOL)


def test_no_profile_yields_flat_index():
    """With no genetic profile, no features fire → η = 1, Var(η) = 0."""
    idx = responder_index(ResponderContext(profile=None, peptide_name="CJC-1295"))
    assert idx.eta == 1.0
    assert idx.var_eta == 0.0
    assert idx.features == ()


def test_required_adapter_failure_propagates():
    """A failure in the anchored (required) genetics adapter must raise, not
    silently degrade the prior — preserving legacy error semantics."""
    import engine.tracking.responder_index as ri

    class Boom:
        name = "boom"
        required = True

        def peptide_mask(self, peptide_name):
            return True

        def features(self, context):
            raise RuntimeError("adapter blew up")

    saved = dict(ri._REGISTRY)
    ri._adapters_loaded = True  # skip auto-discovery
    ri._REGISTRY.clear()
    ri._REGISTRY["boom"] = Boom()
    try:
        with pytest.raises(RuntimeError, match="blew up"):
            responder_index(ResponderContext(profile=None, peptide_name="CJC-1295"))
    finally:
        ri._REGISTRY.clear()
        ri._REGISTRY.update(saved)


def test_optional_adapter_failure_is_isolated():
    """A failure in an optional adapter is skipped (index still computed)."""
    import engine.tracking.responder_index as ri

    class Flaky:
        name = "flaky"
        required = False

        def peptide_mask(self, peptide_name):
            return True

        def features(self, context):
            raise RuntimeError("optional boom")

    profile = generate_synthetic_profile(random.Random(2))
    ri.registered_adapters()  # ensure genetics discovered
    saved = dict(ri._REGISTRY)
    ri._REGISTRY["flaky"] = Flaky()
    try:
        idx = responder_index(
            ResponderContext(profile=profile, peptide_name="CJC-1295")
        )
        # Genetics still fired; the flaky adapter was skipped.
        assert any(f.name == "genetics" for f in idx.features)
    finally:
        ri._REGISTRY.clear()
        ri._REGISTRY.update(saved)


def test_deta_dlinear_matches_sech_squared():
    for x in (-2.0, -0.5, 0.0, 0.3, 1.4):
        expected = R_DELTA_SCALE / (math.cosh(x) ** 2)
        assert math.isclose(_deta_dlinear(x), expected, abs_tol=_ATOL)
