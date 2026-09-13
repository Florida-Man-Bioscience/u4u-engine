"""Knowledge-state timeline from admitted propositions + evidence_links."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from litreview.chain import chain


def timeline(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Oldest year first. Each event is a licensed proposition, not a proof."""
    spans = {r["record_id"]: r for r in records if r.get("kind") == "span"}
    events = []
    for p in records:
        if p.get("kind") != "proposition":
            continue
        ctx = p.get("context") or {}
        span = spans.get(p.get("span_id"), {})
        events.append(
            {
                "year": ctx.get("year"),
                "source_id": ctx.get("source_id"),
                "doi": ctx.get("doi"),
                "pmid": span.get("pmid"),
                "proposition_id": p["record_id"],
                "span_id": p.get("span_id"),
                "text": span.get("locator") or (p.get("args") or [""])[0],
                "admission": p.get("admission"),
            }
        )
    events.sort(key=lambda e: (e["year"] is None, e["year"] or 0, e["proposition_id"]))
    return events


def trace(records: list[dict[str, Any]], start: str) -> list[dict[str, Any]]:
    ids = chain(records, start)
    by = {r["record_id"]: r for r in records}
    out = []
    for i in ids:
        r = by.get(i)
        if not r:
            continue
        out.append({"id": i, "kind": r.get("kind"), "link_kind": r.get("link_kind"), "year": (r.get("context") or {}).get("year")})
    return out
