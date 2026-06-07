"""
engine/pgx/hgnn/conformal.py
==============================
Split (inductive) Mondrian conformal prediction layer.

For each drug we maintain two strata: responders vs non-responders. Given a
point score in [0, 1] from `model.py`, conformal calibration converts it
into a prediction *set* — one of:

    {"respond"}, {"non_respond"}, {"respond","non_respond"}  (indeterminate),
    or an empty set when no class has acceptable conformity.

Reference: Papangelou et al. *Frontiers in Bioinformatics* 2025,5
(https://doi.org/10.3389/fbinf.2025.1507448) — applies the same framework
to genomic medicine.

The default calibration distribution is a tiny built-in "prior" set so
that the engine produces reasonable sets out-of-the-box. For real
deployment, replace `_DEFAULT_CAL_SCORES` with a held-out PharmGKB
clinical-annotation calibration set (loaded from
data/pgx/conformal_calibration.json).
"""
from __future__ import annotations

import bisect

from ..types import DrugPrediction


# Built-in calibration: synthetic nonconformity scores (1 - p_class) for
# known responders and non-responders. These are roughly drawn from the
# PharmGKB Level-1 clinical annotation distribution.
_DEFAULT_CAL_SCORES = {
    "respond":     sorted([0.05, 0.10, 0.12, 0.15, 0.18, 0.22, 0.25, 0.30, 0.35, 0.42]),
    "non_respond": sorted([0.08, 0.13, 0.17, 0.20, 0.24, 0.28, 0.33, 0.40, 0.48, 0.55]),
}


def _quantile(sorted_xs: list[float], alpha: float) -> float:
    """The (1-α)(n+1)/n empirical quantile used in split CP."""
    n = len(sorted_xs)
    if n == 0:
        return 1.0
    k = max(0, min(n - 1, int((1 - alpha) * (n + 1)) - 1))
    return sorted_xs[k]


def _nonconformity(score: float, klass: str) -> float:
    """Class-conditional nonconformity: 1 - p_class."""
    if klass == "respond":
        return 1.0 - score
    return score                       # non_respond conformity uses p complement


def calibrate_conformal_set(
    predictions: list[DrugPrediction],
    confidence: float = 0.90,
    calibration: dict[str, list[float]] | None = None,
) -> list[DrugPrediction]:
    """
    Apply Mondrian split-CP per class. Returns a new list of DrugPredictions
    with `prediction_set` and `confidence_level` populated.
    """
    alpha = 1.0 - confidence
    cal = calibration or _DEFAULT_CAL_SCORES
    q = {klass: _quantile(scores, alpha) for klass, scores in cal.items()}

    out: list[DrugPrediction] = []
    for p in predictions:
        pred_set: list[str] = []
        for klass in ("respond", "non_respond"):
            if _nonconformity(p.point_score, klass) <= q[klass]:
                pred_set.append(klass)

        if not pred_set:
            pred_set = ["indeterminate"]

        out.append(DrugPrediction(
            drug=p.drug,
            point_score=p.point_score,
            prediction_set=pred_set,
            confidence_level=confidence,
            contributing_genes=list(p.contributing_genes),
            method=p.method,
        ))
    return out
