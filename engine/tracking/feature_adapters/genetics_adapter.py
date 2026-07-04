"""
engine/tracking/feature_adapters/genetics_adapter.py
====================================================
The anchored reference feature: the patient's summed genetic weight ``w``.

This wraps today's ``derive_responder_prior`` math as a single feature so the
generalised responder index reduces **exactly** to the legacy model when
genetics is the only adapter firing:

    value  x_g = w                (summed peptide effect weight)
    beta   β_g = 1                (anchored — genetics passes through)
    var    var_g = today_sd² / (Δ·sech²(w))²

With β_g = 1 the linear predictor is ``w`` and the index's delta-method
propagation gives::

    Var(η) = (Δ·sech²(w))² · (β_g² · var_g)
           = (Δ·sech²(w))² · today_sd² / (Δ·sech²(w))²
           = today_sd²

reproducing the legacy responder SD ``today_sd = max(R_MIN_SD,
R_BASE_SD/√(1 + 0.5·n))`` to floating point. The shared ``_deta_dlinear``
helper is used for the back-out so the cancellation is against the identical
float the index will later use.
"""
from __future__ import annotations

import math

from ..genetics import R_BASE_SD, R_MIN_SD
from ..responder_index import (
    Feature,
    ResponderContext,
    _deta_dlinear,
    register_adapter,
)


@register_adapter
class GeneticsAdapter:
    """Summed-weight genetic responder feature (β anchored at 1.0)."""

    name = "genetics"
    # Anchored, non-optional adapter: a failure here is a real regression
    # (the legacy derive_responder_prior raised), so it must propagate rather
    # than degrade the prior to η=1, Var(η)=0. See build_feature_vector.
    required = True

    def peptide_mask(self, peptide_name: str) -> bool:
        # Genetics informs every peptide (the catalog is peptide-keyed, so a
        # peptide with no relevant variants simply yields w = 0, n = 0).
        return True

    def features(self, context: ResponderContext) -> dict[str, Feature]:
        profile = context.profile
        if profile is None:
            return {}
        summary = profile.peptide_effect_summary(context.peptide_name)
        w = float(summary["total_weight"])
        n = int(summary["n_relevant_variants"])

        # Legacy responder SD — the quantity we must reproduce.
        today_sd = max(R_MIN_SD, R_BASE_SD / math.sqrt(1 + 0.5 * n))

        # Back out the feature-space variance that reproduces today_sd through
        # the delta method at the genetics-only operating point (linear = w).
        slope = _deta_dlinear(w)
        var_g = (today_sd * today_sd) / (slope * slope)

        return {
            "genetics": Feature(
                name="genetics",
                value=w,
                beta=1.0,
                variance=var_g,
                source=self.name,
            )
        }
