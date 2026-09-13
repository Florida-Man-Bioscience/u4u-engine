"""Claim-test specifications for Harmonia handoff. Export files only."""

from __future__ import annotations

from typing import Any

REQUIRED = (
    "claim_id",
    "proposition_id",
    "eligible",
    "population",
    "endpoint",
    "data_requirements",
    "provenance",
)


def validate_claim_test(spec: dict[str, Any]) -> list[str]:
    err = [f"missing {k}" for k in REQUIRED if k not in spec]
    if spec.get("eligible") is True:
        if not spec.get("data_requirements"):
            err.append("eligible claim needs data_requirements")
        if spec.get("n") is None and spec.get("n_source") != "unstated":
            err.append("n must be given or n_source=unstated")
    return err


def demo_harmonization_roundtrip(proposition_id: str) -> dict[str, Any]:
    """Manually licensed test: invertibility of a harmonization step.

    Does not run Harmonia. Does not claim verified-on-data.
    """
    return {
        "claim_id": "ct:harmonize-roundtrip",
        "proposition_id": proposition_id,
        "eligible": True,
        "population": "synthetic LongRow fixture",
        "endpoint": "backward(forward(x)) recovers x within engine eps",
        "data_requirements": "feature,sample,value,assay,unit",
        "provenance": "manual; Harmonia Tier-1 QuickCheck only if later executed",
        "n": None,
        "n_source": "unstated",
        "limitations": "passing QuickCheck is not a universal proof",
    }
