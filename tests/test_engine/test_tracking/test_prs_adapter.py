"""
Unit tests for the PRS inflammatory-baseline responder feature adapter.

Covers: registration, the regen/metabolic peptide mask, the signed
standardisation (LOW / MODERATE / HIGH), the modest-mean-shift + SD-widening
honesty contract, and the graceful no-op paths (no ``prs_profile``; present but
under-genotyped). All firing paths feed a pipeline-shaped ``prs_profile`` dict
through ``ResponderContext.extra`` — the only sanctioned source.
"""
from __future__ import annotations

import math

from engine.peptides import get_biomarker_panel
from engine.tracking.feature_adapters.prs_adapter import (
    _BETA,
    _MASKED_PEPTIDES,
    _MIN_INFLAM_VARIANTS,
    PRSInflammatoryBaselineAdapter,
)
from engine.tracking.genetics import R_DELTA_SCALE
from engine.tracking.responder_index import (
    ResponderContext,
    registered_adapters,
    responder_index,
)

ADAPTER_NAME = "prs_inflammatory_baseline"


def _prs_profile(score: float, *, variants_found: int = 8) -> dict:
    """A minimal pipeline-shaped ``prs_profile`` carrying an INF-PRS score."""
    return {
        "trait_scores": {
            "systemic_inflammation": {
                "prs_score": score,
                "variants_found": variants_found,
            }
        }
    }


def _ctx(peptide: str, extra: dict | None = None) -> ResponderContext:
    # profile stays None: this adapter must never touch the tracking profile.
    return ResponderContext(peptide_name=peptide, profile=None, extra=extra or {})


# ── Registration + mask ──────────────────────────────────────────────────────

def test_adapter_is_registered_and_optional():
    adapters = registered_adapters()
    assert ADAPTER_NAME in adapters
    assert getattr(adapters[ADAPTER_NAME], "required", False) is False


def test_masked_peptide_names_are_canonical():
    """Every name in the mask must be a real peptide in the canonical panel
    registry. This binds the hardcoded subset to a source of truth so a peptide
    rename surfaces as a test failure instead of silently disabling the feature.
    """
    for pep in _MASKED_PEPTIDES:
        assert get_biomarker_panel(pep) is not None, (
            f"masked peptide {pep!r} has no canonical biomarker panel — "
            "the catalog spelling drifted from the mask"
        )


def test_peptide_mask_covers_regen_metabolic_only():
    a = PRSInflammatoryBaselineAdapter()
    for pep in ("BPC-157", "TB-500", "GHK-Cu", "MOTS-c", "AOD-9604",
                "Semaglutide", "Tirzepatide", "Liraglutide"):
        assert a.peptide_mask(pep) is True, pep
    # Anti-inflammatory-target peptides are excluded (inflammation is their
    # target, so a dampening sign would be wrong).
    for pep in ("KPV", "LL-37", "Thymosin Alpha-1", "Selank", "CJC-1295"):
        assert a.peptide_mask(pep) is False, pep


# ── Signed standardisation: LOW / MODERATE / HIGH ────────────────────────────

def test_high_inflammation_dampens_response():
    a = PRSInflammatoryBaselineAdapter()
    feats = a.features(_ctx("BPC-157", {"prs_profile": _prs_profile(0.85)}))
    assert ADAPTER_NAME in feats
    f = feats[ADAPTER_NAME]
    # HIGH score → positive value; β < 0 → negative linear contribution (damp).
    assert f.value > 0
    assert f.beta == _BETA < 0
    assert f.beta * f.value < 0


def test_low_inflammation_lifts_response():
    a = PRSInflammatoryBaselineAdapter()
    feats = a.features(_ctx("MOTS-c", {"prs_profile": _prs_profile(0.15)}))
    f = feats[ADAPTER_NAME]
    # LOW score → negative value; β < 0 → positive linear contribution.
    assert f.value < 0
    assert f.beta * f.value > 0


def test_moderate_inflammation_is_near_neutral():
    a = PRSInflammatoryBaselineAdapter()
    feats = a.features(_ctx("Semaglutide", {"prs_profile": _prs_profile(0.5)}))
    f = feats[ADAPTER_NAME]
    assert math.isclose(f.value, 0.0, abs_tol=1e-9)


def test_monotonic_in_score():
    a = PRSInflammatoryBaselineAdapter()
    vals = [
        a.features(_ctx("BPC-157", {"prs_profile": _prs_profile(s)}))[ADAPTER_NAME].value
        for s in (0.1, 0.4, 0.6, 0.9)
    ]
    assert vals == sorted(vals)


# ── Honesty contract: modest mean shift, widened SD ──────────────────────────

def test_mean_shift_stays_modest():
    """Even at an extreme HIGH baseline the shift in η is small (~0.12)."""
    ctx = _ctx("BPC-157", {"prs_profile": _prs_profile(1.0)})
    idx = responder_index(ctx)
    # Genetics no-ops (profile=None) so η reflects the PRS feature alone.
    shift = abs(idx.eta - 1.0)
    assert shift < 0.15, shift
    # η stays inside the bounded band.
    assert 1.0 - R_DELTA_SCALE <= idx.eta <= 1.0 + R_DELTA_SCALE


def test_feature_widens_variance():
    """A fired PRS feature contributes positive Var(η) (SD half of contract)."""
    fired = responder_index(_ctx("BPC-157", {"prs_profile": _prs_profile(0.85)}))
    assert fired.var_eta > 0.0
    assert any(f.name == ADAPTER_NAME for f in fired.features)


# ── Graceful no-op paths ─────────────────────────────────────────────────────

def test_no_extra_is_noop():
    a = PRSInflammatoryBaselineAdapter()
    assert a.features(_ctx("BPC-157")) == {}


def test_missing_prs_profile_is_noop():
    a = PRSInflammatoryBaselineAdapter()
    assert a.features(_ctx("BPC-157", {"something_else": 1})) == {}


def test_under_genotyped_prs_is_noop():
    """Fewer than the minimum panel SNPs genotyped → contribute nothing."""
    a = PRSInflammatoryBaselineAdapter()
    extra = {"prs_profile": _prs_profile(0.9, variants_found=_MIN_INFLAM_VARIANTS - 1)}
    assert a.features(_ctx("BPC-157", extra)) == {}


def test_malformed_prs_profile_is_noop():
    a = PRSInflammatoryBaselineAdapter()
    for bad in ({"prs_profile": None},
                {"prs_profile": {}},
                {"prs_profile": {"trait_scores": {}}},
                {"prs_profile": {"trait_scores": {"systemic_inflammation": {}}}}):
        assert a.features(_ctx("BPC-157", bad)) == {}


def test_unmasked_peptide_never_contributes_via_index():
    """A masked-out peptide gets no PRS feature even with data present."""
    idx = responder_index(_ctx("KPV", {"prs_profile": _prs_profile(0.9)}))
    assert all(f.name != ADAPTER_NAME for f in idx.features)
