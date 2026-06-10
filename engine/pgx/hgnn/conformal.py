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

Conformal validity is conditional: a split-conformal prediction set only
achieves its nominal coverage when the calibration scores are *exchangeable*
with the deployment population. A guarantee computed on invented numbers is
not a guarantee at all. Therefore this module will only emit a
confidence-bearing prediction set when a **real** calibration set is available
(loaded from ``data/pgx/conformal_calibration.json`` or supplied explicitly).
With no real calibration set, predictions are returned in an explicit
``["uncalibrated"]`` state with ``confidence_level=None`` so that no false
statistical guarantee is presented downstream.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from ..types import DrugPrediction

log = logging.getLogger(__name__)

# Where a real, held-out calibration set would live. Schema:
#   {"respond": [floats...], "non_respond": [floats...]}
# containing nonconformity scores from labeled, held-out PharmGKB clinical
# annotations that are exchangeable with the deployment population.
_CALIBRATION_PATH = os.getenv(
    "PGX_CONFORMAL_CALIBRATION",
    str(Path(__file__).resolve().parents[3] / "data" / "pgx" / "conformal_calibration.json"),
)

_UNCALIBRATED_SET = ["uncalibrated"]


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


def load_real_calibration(path: str | None = None) -> dict[str, list[float]] | None:
    """
    Load a real held-out calibration set if one is present on disk.

    Returns the calibration dict, or None when no valid file exists. A missing
    file is the normal case until a real calibration set has been assembled and
    validated — callers must treat None as "no conformal guarantee available".
    """
    p = Path(path or _CALIBRATION_PATH)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if (
            isinstance(data, dict)
            and isinstance(data.get("respond"), list)
            and isinstance(data.get("non_respond"), list)
            and data["respond"] and data["non_respond"]
        ):
            return {
                "respond": sorted(float(x) for x in data["respond"]),
                "non_respond": sorted(float(x) for x in data["non_respond"]),
            }
        log.error("conformal calibration file %s is malformed; ignoring", p)
    except Exception as e:  # pragma: no cover — defensive
        log.error("failed to load conformal calibration %s: %s", p, e)
    return None


def calibrate_conformal_set(
    predictions: list[DrugPrediction],
    confidence: float = 0.90,
    calibration: dict[str, list[float]] | None = None,
    calibration_is_real: bool = False,
) -> list[DrugPrediction]:
    """
    Apply Mondrian split-CP per class **only** when backed by a real,
    exchangeable calibration set.

    Calibration source resolution:
      1. ``calibration`` argument with ``calibration_is_real=True`` (e.g. tests
         or an injected validated set);
      2. a validated file at ``data/pgx/conformal_calibration.json``;
      3. otherwise → no calibration. Predictions are returned as
         ``prediction_set=["uncalibrated"]`` with ``confidence_level=None`` so
         that the absence of a coverage guarantee is explicit and honest.

    The point score is always preserved; only the *set* and its claimed
    confidence are gated on real calibration.
    """
    if calibration is not None and calibration_is_real:
        cal = calibration
    else:
        cal = load_real_calibration()

    if not cal:
        # No real calibration available — do not fabricate a guarantee.
        return [
            DrugPrediction(
                drug=p.drug,
                point_score=p.point_score,
                prediction_set=list(_UNCALIBRATED_SET),
                confidence_level=None,
                contributing_genes=list(p.contributing_genes),
                method=p.method,
            )
            for p in predictions
        ]

    alpha = 1.0 - confidence
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
