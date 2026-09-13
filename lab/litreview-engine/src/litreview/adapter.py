"""Admit extracted sentences as logic-v1 records. No invented biology."""

from __future__ import annotations

import re
from typing import Any

from litreview import SCHEMA_V1

_CLAIM_CUE = re.compile(
    r"\b(we (show|conclude|find|found|propose|present|demonstrate)|"
    r"this (paper|review|study)|harmoniz|therefore|our (results|analysis))\b",
    re.I,
)


def _span_id(source: str, sid: str) -> str:
    return f"span:{source}:{sid}"


def _prop_id(source: str, sid: str) -> str:
    return f"proposition:{source}:{sid}"


def admit_extract(
    extract: dict[str, Any],
    *,
    source_id: str,
    year: int,
    doi: str | None,
    pmid: str | None,
    corpus_id: str,
    max_mapped: int = 40,
) -> list[dict[str, Any]]:
    """Map cue-bearing sentences; defer the rest. pmid may be null."""
    recs: list[dict[str, Any]] = []
    mapped = 0
    for row in extract.get("sentences") or []:
        text = row["sentence"]
        sid = row["id"]
        span = {
            "record_id": _span_id(source_id, sid),
            "corpus_id": corpus_id,
            "schema_version": SCHEMA_V1,
            "kind": "span",
            "pmid": pmid,
            "locator": text,
            "sha256": extract.get("sha256") or "unknown",
            "access": "oa",
            "page": row.get("page"),
        }
        recs.append(span)
        is_claim = bool(_CLAIM_CUE.search(text)) and mapped < max_mapped
        status = "selected" if is_claim else "deferred"
        recs.append(
            {
                "record_id": f"selection:{source_id}:{sid}",
                "corpus_id": corpus_id,
                "schema_version": SCHEMA_V1,
                "kind": "selection",
                "span_id": span["record_id"],
                "status": status,
            }
        )
        if is_claim:
            mapped += 1
            recs.append(
                {
                    "record_id": _prop_id(source_id, sid),
                    "corpus_id": corpus_id,
                    "schema_version": SCHEMA_V1,
                    "kind": "proposition",
                    "predicate": "states",
                    "args": [text[:180]],
                    "context": {
                        "year": year,
                        "doi": doi,
                        "source_id": source_id,
                        "taxon": None,
                        "assay": None,
                    },
                    "span_id": span["record_id"],
                    "admission": "admitted",
                }
            )
    return recs


def link_shared_cues(
    records: list[dict[str, Any]],
    *,
    cue: str,
    earlier_source: str,
    later_source: str,
) -> list[dict[str, Any]]:
    """If later and earlier propositions both contain cue, add rests_on with later quote."""
    cue_l = cue.lower()
    props = [r for r in records if r.get("kind") == "proposition"]
    spans = {r["record_id"]: r for r in records if r.get("kind") == "span"}
    early = [
        p
        for p in props
        if (p.get("context") or {}).get("source_id") == earlier_source
        and cue_l in " ".join(p.get("args") or []).lower()
    ]
    late = [
        p
        for p in props
        if (p.get("context") or {}).get("source_id") == later_source
        and cue_l in " ".join(p.get("args") or []).lower()
    ]
    extra = []
    if not early or not late:
        return extra
    src, dst = late[0], early[0]
    span = spans.get(src["span_id"])
    extra.append(
        {
            "record_id": f"evidence_link:{later_source}-rests_on-{earlier_source}",
            "corpus_id": src["corpus_id"],
            "schema_version": SCHEMA_V1,
            "kind": "evidence_link",
            "src_id": src["record_id"],
            "dst_id": dst["record_id"],
            "link_kind": "rests_on",
            "span_id": src["span_id"],
            "quote": (span or {}).get("locator"),
            "admission": "admitted",
        }
    )
    return extra
