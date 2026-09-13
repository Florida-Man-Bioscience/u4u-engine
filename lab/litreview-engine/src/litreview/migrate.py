"""Non-destructive v0 → quarantine. Never invent admission=admitted."""

from __future__ import annotations

from typing import Any


def migrate(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []
    for r in records:
        if r.get("schema_version") == "logic-v0" and "admission" not in r:
            q = dict(r)
            q["admission"] = "quarantined"
            q["quarantine_reason"] = "missing admission dimension; not invented"
            quarantined.append(q)
        else:
            kept.append(r)
    return {"kept": kept, "quarantined": quarantined}
