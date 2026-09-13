"""Immutable revisions: superseding a record stale-marks dependents. Not a prover."""

from __future__ import annotations

from typing import Any

from litreview.revisions import revision_matches


def replay(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    superseded = {r["supersedes"] for r in records if r.get("supersedes")}
    out = [dict(r) for r in records]
    index = {r["record_id"]: r for r in out if "record_id" in r}
    for rr in out:
        if rr.get("kind") != "evidence_link":
            continue
        if rr.get("link_kind") == "justified_by":
            stale = any(
                rr.get(field) in superseded
                for field in ("src_id", "dst_id", "claim_ref", "argument_ref")
            )
            src = index.get(rr.get("src_id"))
            claim = index.get(rr.get("claim_ref"))
            argument = index.get(rr.get("argument_ref"))
            if src is None or not revision_matches(rr.get("method_revision"), src.get("revision")):
                stale = True
            if claim is None or not revision_matches(
                rr.get("claim_revision"), claim.get("revision", 1)
            ):
                stale = True
            if src is not None and claim is not None and not revision_matches(
                claim.get("method_revision"), src.get("revision")
            ):
                stale = True
            if argument is None or not revision_matches(
                rr.get("argument_revision"), argument.get("argument_revision", 1)
            ):
                stale = True
            if stale:
                rr["review_state"] = "stale"
                rr["admission"] = "stale"
        elif rr.get("src_id") in superseded or rr.get("dst_id") in superseded:
            rr["admission"] = "stale"
    return out
