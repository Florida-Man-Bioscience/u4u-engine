"""Walk licensed evidence links. Not a vis-network projection."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any


def grow(records: list[dict[str, Any]]) -> dict[str, list[tuple[str, str, str]]]:
    """Adjacency: proposition id -> list of (link_id, kind, other_id)."""
    adj: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for r in records:
        if r.get("kind") != "evidence_link":
            continue
        src, dst, kind, rid = r["src_id"], r["dst_id"], r["link_kind"], r["record_id"]
        adj[src].append((rid, kind, dst))
        adj[dst].append((rid, kind, src))
    return dict(adj)


def chain(records: list[dict[str, Any]], start: str, *, limit: int = 64) -> list[str]:
    """BFS through evidence_link and derivation conclusions. Returns record ids."""
    by_id = {r["record_id"]: r for r in records}
    if start not in by_id:
        raise KeyError(start)
    deriv_next: dict[str, list[str]] = defaultdict(list)
    for r in records:
        if r.get("kind") == "derivation":
            deriv_next[r["conclusion_id"]].append(r["record_id"])
            for pid in r.get("premise_ids") or []:
                prem = by_id.get(pid)
                if prem:
                    deriv_next[prem.get("proposition_id", "")].append(r["record_id"])
    adj = grow(records)
    seen = {start}
    out = [start]
    q: deque[str] = deque([start])
    while q and len(out) < limit:
        cur = q.popleft()
        neighbors: list[str] = []
        for link_id, _kind, other in adj.get(cur, []):
            neighbors.append(link_id)
            neighbors.append(other)
        for did in deriv_next.get(cur, []):
            neighbors.append(did)
            d = by_id[did]
            neighbors.append(d["conclusion_id"])
        for n in neighbors:
            if n and n not in seen:
                seen.add(n)
                out.append(n)
                q.append(n)
    return out
