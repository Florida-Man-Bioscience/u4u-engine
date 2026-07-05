"""
Unit tests for the BPC-157 composite responder feature adapter
(``engine.tracking.feature_adapters.bpc157_adapter``).

The adapter is peptide-masked to BPC-157 and optional (a graceful no-op when no
BPC-157 data is on the context). We drive the low/high-composite cases with
``profile=None`` so the genetics adapter contributes nothing and the BPC-157
feature is the *sole* contributor — η and Var(η) are then deterministic
functions of the composite alone, with no operating-point interaction from
genetics (cf. the frozen §2.3 composition rule).
"""
from __future__ import annotations

import math

from engine.annotators.bpc157_predictor import predict_bpc157_response
from engine.tracking.feature_adapters.bpc157_adapter import (
    _FEATURE_NAME,
    _PEPTIDE_NAME,
    _RIDGE_BETA,
    _SPREAD,
    _UNCERTAIN_THRESHOLD,
    BPC157CompositeAdapter,
)
from engine.tracking.responder_index import (
    ResponderContext,
    registered_adapters,
    responder_index,
)

_ATOL = 1e-12

# Variant fixtures that exercise the real predictor's tier scale.
# One partial pathway hit (COMT = 1/4 of the dopamine pathway = 0.25) plus its
# modifier rsID (weight 0.5) → composite 0.75, in the "uncertain" tier.
_LOW_VARIANTS = [
    {"genes": ["COMT"], "rsid": "rs4680"},          # dopamine pathway, weight 0.5
]
# Many pathway genes + high-weight modifier rsIDs → high composite (likely_good).
_HIGH_VARIANTS = [
    {"genes": ["NOS3"], "rsid": "rs1799983"},       # NO/eNOS, modifier weight 1.5
    {"genes": ["IL6"], "rsid": "rs1800795"},        # inflammation, modifier 1.5
    {"genes": ["TNF"], "rsid": "rs1800629"},        # inflammation, modifier 1.5
    {"genes": ["VEGFA"], "rsid": "rs2010963"},      # angiogenesis, modifier 1.0
    {"genes": ["COL1A1"], "rsid": "rs1800012"},     # collagen, modifier 1.0
    {"genes": ["HMOX1"], "rsid": "rs2071746"},      # antioxidant, modifier 1.0
]
# A gene with no BPC-157 relevance at all → predictor returns empty overlap.
_IRRELEVANT_VARIANTS = [
    {"genes": ["BRCA1"], "rsid": "rs80357906"},
]


def _feature_for(variants, *, peptide=_PEPTIDE_NAME):
    ctx = ResponderContext(
        peptide_name=peptide, profile=None, extra={"bpc157": variants}
    )
    return BPC157CompositeAdapter().features(ctx)


# ── registration & masking ──────────────────────────────────────────────────

def test_adapter_is_registered_and_optional():
    adapters = registered_adapters()
    assert "bpc157_composite" in adapters
    adapter = adapters["bpc157_composite"]
    assert getattr(adapter, "required", False) is False


def test_peptide_mask_only_bpc157():
    adapter = BPC157CompositeAdapter()
    assert adapter.peptide_mask("BPC-157") is True
    assert adapter.peptide_mask(" BPC-157 ") is True   # tolerant of whitespace
    for other in ("CJC-1295", "MOTS-c", "GHK-Cu", "TB-500", "", "bpc-157"):
        assert adapter.peptide_mask(other) is False


# ── standardisation: low vs high composite ──────────────────────────────────

def test_low_composite_feature_matches_standardisation():
    # Anchored to literal values (not recomputed from the adapter's own
    # constants) so a wrong _SPREAD / _UNCERTAIN_THRESHOLD or a broken
    # standardisation formula fails loudly instead of shipping green.
    prediction = predict_bpc157_response(_LOW_VARIANTS)
    assert math.isclose(prediction["composite_score"], 0.75, abs_tol=1e-9)
    feats = _feature_for(_LOW_VARIANTS)
    assert set(feats) == {_FEATURE_NAME}
    f = feats[_FEATURE_NAME]
    # x = (0.75 − 0.5) / 2.5 = 0.1
    assert math.isclose(f.value, 0.1, abs_tol=1e-9)
    assert f.beta == _RIDGE_BETA
    assert f.variance > 0.0
    assert f.source == "bpc157_composite"


def test_high_composite_gives_larger_positive_feature_than_low():
    low = _feature_for(_LOW_VARIANTS)[_FEATURE_NAME]
    high = _feature_for(_HIGH_VARIANTS)[_FEATURE_NAME]
    # Higher composite → strictly larger (more positive) standardised value.
    assert high.value > low.value
    # The high case clears the "likely_good" tier (composite ≥ 3.0 → x ≥ 1.0).
    assert high.value >= (3.0 - _UNCERTAIN_THRESHOLD) / _SPREAD


def test_index_eta_moves_up_with_composite_profile_none():
    """With profile=None the BPC-157 feature is the sole contributor, so η is a
    deterministic, monotone function of the composite (β>0, x increasing)."""
    low_ctx = ResponderContext(
        peptide_name=_PEPTIDE_NAME, profile=None, extra={"bpc157": _LOW_VARIANTS}
    )
    high_ctx = ResponderContext(
        peptide_name=_PEPTIDE_NAME, profile=None, extra={"bpc157": _HIGH_VARIANTS}
    )
    low_idx = responder_index(low_ctx)
    high_idx = responder_index(high_ctx)

    # Only the bpc157 feature fired (genetics no-ops on a None profile), so η
    # is driven by the composite alone.
    assert [f.name for f in high_idx.features] == [_FEATURE_NAME]
    # Higher composite → stronger responder (η rises above baseline).
    assert high_idx.eta > low_idx.eta
    assert high_idx.eta > 1.0
    # A speculative feature carries variance, so Var(η) is strictly positive
    # (an unbounded-confidence feature would report var 0) — it widens, not
    # sharpens, the responder. (The η/Var(η) closed form itself is covered by
    # test_responder_index.py; we don't re-assert the engine here.)
    assert high_idx.var_eta > 0.0


# ── mask-off & no-data no-ops ───────────────────────────────────────────────

def test_non_bpc157_peptide_masked_off_no_feature():
    """Even with BPC-157 data on the context, a non-BPC-157 peptide never
    collects this feature (peptide_mask gates it out in build_feature_vector)."""
    ctx = ResponderContext(
        peptide_name="CJC-1295", profile=None, extra={"bpc157": _HIGH_VARIANTS}
    )
    idx = responder_index(ctx)
    assert all(f.name != _FEATURE_NAME for f in idx.features)


def test_no_bpc157_data_is_noop():
    """No extra['bpc157'] → the adapter contributes nothing (does not raise)."""
    ctx = ResponderContext(peptide_name=_PEPTIDE_NAME, profile=None)
    assert BPC157CompositeAdapter().features(ctx) == {}
    idx = responder_index(ctx)
    # Nothing fired at all → degenerate flat index.
    assert idx.eta == 1.0
    assert idx.var_eta == 0.0
    assert idx.features == ()


def test_irrelevant_variants_are_noop():
    """Variants with no BPC-157-relevant loci must not fire (a composite of 0
    from absence is not evidence of non-response — it must not pull η down)."""
    assert _feature_for(_IRRELEVANT_VARIANTS) == {}


def test_accepts_precomputed_prediction_dict():
    """The pipeline's display prediction dict is accepted directly (no recompute)."""
    prediction = predict_bpc157_response(_HIGH_VARIANTS)
    feats = _feature_for(prediction)
    assert set(feats) == {_FEATURE_NAME}
    expected_x = (prediction["composite_score"] - _UNCERTAIN_THRESHOLD) / _SPREAD
    assert math.isclose(feats[_FEATURE_NAME].value, expected_x, abs_tol=_ATOL)
