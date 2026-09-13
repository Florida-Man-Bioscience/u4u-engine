"""Filter admitted records into Harmonia-shaped exports. No Harmonia import."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from litreview.validate import validate_batch


def exportable(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    errors = validate_batch(records)
    if errors:
        raise ValueError(errors)
    admitted = []
    for r in records:
        if r.get("admission") in {"quarantined", "stale"}:
            continue
        if r.get("admitted") is not True and r.get("admission") != "admitted":
            continue
        loss = r.get("loss_report") or {}
        if loss.get("material"):
            continue
        admitted.append(r)
    return {
        "long_row": [r for r in admitted if r["kind"] == "long_row"],
        "rule_candidate": [r for r in admitted if r["kind"] == "rule_candidate"],
        "law_obligation": [r for r in admitted if r["kind"] == "law_obligation"],
    }


def long_rows_csv(rows: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["feature", "sample", "value", "assay", "unit", "corpus_id", "record_id"])
    for r in rows:
        w.writerow(
            [r["feature"], r["sample"], r["value"], r["assay"], r["unit"], r["corpus_id"], r["record_id"]]
        )
    return buf.getvalue()


def obligations_jsonl(rows: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)
