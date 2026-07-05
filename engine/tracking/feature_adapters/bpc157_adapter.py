"""
engine/tracking/feature_adapters/bpc157_adapter.py
==================================================
BPC-157 composite responder feature — Phase-1 fan-out unit.

Turns the existing offline BPC-157 predictor
(:func:`engine.annotators.bpc157_predictor.predict_bpc157_response`) into a
responder feature for the Hierarchical Bayesian Responder Index (HBRI). The
predictor's ``composite_score`` is a real, additive peptide-effect signal
(pathway overlap + rsID modifier weights; tier thresholds 0.5 / 1.5 / 3.0)
that today is only surfaced for display. Here it enters ``η`` (the prior mean)
as a single standardised feature, **peptide-masked to BPC-157 only**.

Standardisation
---------------
The composite is centred on the predictor's "uncertain" tier threshold and
scaled by the uncertain→likely_good span so ``x`` is O(1) and ``βᵀx`` stays
well inside the ``tanh`` linear region::

    x = (composite_score − UNCERTAIN_THRESHOLD) / SPREAD
      = (composite_score − 0.5) / 2.5

so composite 0.5 → x=0 (neutral), composite 3.0 ("likely_good") → x=1.0.
Higher composite → larger positive ``x`` → stronger responder, as required.

Honesty contract
----------------
BPC-157 has **no validated human genetic predictor** (see the predictor's
disclaimer). The feature therefore:
  - enters the prior mean with a **wide ridge coefficient** ``β`` (a modest,
    shrunk pull — not the anchored β=1 of genetics), and
  - carries a **wide feature variance** ``var`` so it *widens* the responder
    uncertainty rather than sharpening it (Σ β²·var grows Var(βᵀx); cf. the
    frozen §2.3 composition rule — the net effect on ``Var(η)`` also depends
    on the joint operating point, so we do not claim a monotone SD increase).

Data sourcing & the persistence gap
------------------------------------
The faithful composite is computed by the pipeline over the patient's *full*
annotated genome. That genome is **not** persisted to the tracking store —
``patient_genetics.profile_json`` holds only the ~25-SNP catalog
``GeneticProfile`` (see ``engine/tracking/service.py::set_genetic_profile`` and
``profile_from_job.build_profile_from_job_results``), and the display composite
is not persisted at all. Recomputing off the catalog profile would be
unfaithful (wrong variant footprint) *and* would break the frozen genetics-only
golden numbers for BPC-157 (the synthetic ``VARIANT_CATALOG`` carries BPC-157
pathway genes). So this adapter deliberately sources only from an explicit
``context.extra["bpc157"]`` channel and is a **graceful no-op** whenever that
channel is absent — which, until the pipeline wires the composite (or raw
variants) through ``ResponderContext.extra``, is every production prediction.
It is optional (``required = False``) and, being peptide-masked, contributes
nothing to any non-BPC-157 prediction by design.

``context.extra["bpc157"]`` may be either:
  - a ``list`` of annotated variant dicts (``genes`` / ``rsid`` fields) — the
    adapter recomputes via ``predict_bpc157_response(...)``; or
  - a prediction ``dict`` already produced by ``predict_bpc157_response`` (the
    pipeline computes this for display) — used directly, no recompute.
"""
from __future__ import annotations

from typing import Any

from engine.annotators.bpc157_predictor import predict_bpc157_response

from ..responder_index import Feature, ResponderContext, register_adapter

# Canonical peptide name (matches the tracking panel, seed scenarios, and the
# genetics catalog's peptide_effects keys).
_PEPTIDE_NAME = "BPC-157"

# Standardisation of the composite score onto an O(1) feature axis, anchored to
# the predictor's own tier thresholds (_TIER_THRESHOLDS: uncertain=0.5,
# likely_good=3.0).
_UNCERTAIN_THRESHOLD = 0.5           # centre: the "uncertain" tier boundary
_SPREAD = 2.5                        # scale: uncertain → likely_good span

# Wide ridge coefficient — a shrunk pull on the prior mean (NOT the anchored
# β=1 of the genetics reference feature). Kept small so even a "likely_good"
# composite (x=1) nudges the linear predictor by only ~0.35.
_RIDGE_BETA = 0.35

# Wide feature-value variance (in standardised x-units). BPC-157 responder
# prediction is speculative/unvalidated, so the feature reports low confidence;
# this enlarges Var(βᵀx) = Σ β²·var, keeping the model honest about how little
# this signal is actually known to mean.
_FEATURE_VAR = 1.0

_FEATURE_NAME = "bpc157_composite"


def _resolve_prediction(payload: Any) -> dict[str, Any] | None:
    """Coerce an ``extra['bpc157']`` payload into a prediction dict.

    Accepts a raw variant list or a pre-computed prediction dict. Returns
    ``None`` if the payload carries no usable data.
    """
    if isinstance(payload, list):
        return predict_bpc157_response(payload)
    if isinstance(payload, dict) and "composite_score" in payload:
        # Already a prediction (e.g. the pipeline's display payload).
        return payload
    return None


@register_adapter
class BPC157CompositeAdapter:
    """Peptide-masked BPC-157 composite-score responder feature."""

    name = _FEATURE_NAME
    # Optional, peptide-masked: absent for every non-BPC-157 prediction by
    # design, and a graceful no-op when no BPC-157 data is supplied. A failure
    # here must never sink the index (unlike the anchored genetics adapter).
    required = False

    def peptide_mask(self, peptide_name: str) -> bool:
        return (peptide_name or "").strip() == _PEPTIDE_NAME

    def features(self, context: ResponderContext) -> dict[str, Feature]:
        prediction = _resolve_prediction(context.extra.get("bpc157"))
        if prediction is None:
            return {}  # no BPC-157 data on this context → contribute nothing

        # Only fire when at least one BPC-157-relevant locus actually
        # contributed. A composite of ~0 from *absence* of relevant variants is
        # not evidence of non-response, so it must not pull the responder down.
        if not (prediction.get("pathways_affected") or prediction.get("candidate_factors")):
            return {}

        composite = float(prediction.get("composite_score", 0.0))
        value = (composite - _UNCERTAIN_THRESHOLD) / _SPREAD

        return {
            _FEATURE_NAME: Feature(
                name=_FEATURE_NAME,
                value=value,
                beta=_RIDGE_BETA,
                variance=_FEATURE_VAR,
                source=self.name,
            )
        }
