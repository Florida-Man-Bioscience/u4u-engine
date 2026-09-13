"""Rebuildable vis projection. Not SSoT."""

from __future__ import annotations

from typing import Any


def vis_nodes(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "projection": True,
        "kind": "vis-network",
        "nodes": [
            {"id": r.get("record_id"), "kind": r.get("kind")}
            for r in records
            if r.get("record_id")
        ],
    }


def admit(obj: dict[str, Any]) -> list[str]:
    if obj.get("projection"):
        return ["projection cannot be admitted as SSoT"]
    return []
