"""Validation helpers for paper figure-panel and Methods recipes."""

from __future__ import annotations

from typing import Any

from litreview import EXTRACTION_STATES


GENERALIZATION_DIMENSIONS = ("taxon", "system", "assay", "io", "transfer")
GENERALIZATION_SOURCE_BASES = (
    "author-stated",
    "extraction-inference",
    "revision-proposal",
)


_PANEL_SLOTS = (
    "purpose",
    "meaning",
    "methods_used",
    "experimental_design",
    "evidenced_result",
    "locators",
)

_METHODS_SLOTS = (
    "identity",
    "operations",
    "parameters",
    "io",
    "produced",
    "locators",
)


def panel_slots() -> tuple[str, ...]:
    """Return the required slots for a figure-panel recipe."""

    return _PANEL_SLOTS


def methods_slots() -> tuple[str, ...]:
    """Return the required slots for a Methods recipe."""

    return _METHODS_SLOTS


def slot_state(slot: Any) -> str | None:
    """Return a recipe slot's extraction state, if it has one."""

    if not isinstance(slot, dict):
        return None
    return slot.get("state")
