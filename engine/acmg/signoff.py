"""
engine/acmg/signoff.py
======================
Clinician/laboratory sign-out for the automated ACMG/AMP evidence assembly.

The automated classification is a *draft*. For clinical use a qualified
professional must review the evidence and either approve the draft or amend it,
and that decision must be recorded (who, when, what, why). This module is the
domain logic for that human-in-the-loop step; a thin API layer records it.

NOTE: This records a basic attributable sign-out. A full 21 CFR Part 11
electronic-signature implementation (identity binding, tamper-evident audit,
non-repudiation) is a separate piece of work — see the validation plan §8.5.

Public interface
----------------
    apply_signoff(acmg_result, reviewer, action, final_classification=None,
                  notes="", signed_at=None) -> dict
"""

from __future__ import annotations

from datetime import datetime, timezone

from .criteria import Classification

VALID_ACTIONS = ("approve", "amend")
_VALID_CLASSIFICATIONS = {c.value for c in Classification}


def apply_signoff(
    acmg_result: dict,
    reviewer: str,
    action: str,
    final_classification: str | None = None,
    notes: str = "",
    signed_at: str | None = None,
) -> dict:
    """
    Return a new ACMG result with a recorded sign-out.

    - ``action="approve"``: the automated classification becomes final.
    - ``action="amend"``: ``final_classification`` (a valid five-tier label)
      overrides the automated classification.

    Raises ValueError on invalid reviewer/action/classification.
    """
    if not reviewer or not str(reviewer).strip():
        raise ValueError("A reviewer identity is required to sign out.")
    if action not in VALID_ACTIONS:
        raise ValueError(f"Invalid action {action!r}. Expected one of {VALID_ACTIONS}.")

    automated = acmg_result.get("classification")
    if action == "approve":
        final = automated
    else:  # amend
        if not final_classification:
            raise ValueError("An amended classification is required when action='amend'.")
        if final_classification not in _VALID_CLASSIFICATIONS:
            raise ValueError(
                f"Invalid classification {final_classification!r}. "
                f"Expected one of {sorted(_VALID_CLASSIFICATIONS)}."
            )
        final = final_classification

    record = {
        "reviewer": str(reviewer).strip(),
        "action": action,
        "automated_classification": automated,
        "final_classification": final,
        "notes": str(notes or "").strip(),
        "signed_at": signed_at or datetime.now(timezone.utc).isoformat(),
    }

    updated = dict(acmg_result)
    updated["sign_out"] = record
    updated["final_classification"] = final
    updated["status"] = "signed_off"
    updated["requires_human_review"] = False
    return updated
