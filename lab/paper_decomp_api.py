"""HTTP helpers for the paper-decomposition engine inside the lab jail."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parent / "litreview-engine" / "src"
if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))

from litreview import ENGINE_VERSION  # noqa: E402
from litreview.cli import paper_decomposition_coverage  # noqa: E402
from litreview.validate import validate_batch  # noqa: E402


def engine_info() -> dict:
    return {
        "id": "paper-decomposition",
        "engine_version": ENGINE_VERSION,
        "cli": "python3 -m litreview",
    }


def _records_from_payload(payload: dict) -> tuple[list[dict] | None, str | None]:
    if isinstance(payload.get("records"), list):
        recs = payload["records"]
        if not all(isinstance(r, dict) for r in recs):
            return None, "records_must_be_objects"
        return recs, None
    jsonl = payload.get("jsonl")
    if isinstance(jsonl, str):
        recs: list[dict] = []
        for i, line in enumerate(jsonl.splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                return None, f"bad_jsonl_line:{i}"
            if not isinstance(rec, dict):
                return None, f"bad_jsonl_line:{i}"
            recs.append(rec)
        return recs, None
    return None, "need_records_or_jsonl"


def admit(payload: dict) -> tuple[int, dict]:
    recs, err = _records_from_payload(payload)
    if err or recs is None:
        return 400, {"ok": False, "error": err or "need_records_or_jsonl"}
    errors = validate_batch(recs)
    if errors:
        return 400, {"ok": False, "error": "validation_failed", "errors": errors}
    counts = Counter(rec.get("sort") for rec in recs if rec.get("sort"))
    coverage = paper_decomposition_coverage(recs)
    return 200, {
        "ok": True,
        "engine_version": ENGINE_VERSION,
        "admitted": len(recs),
        "sorts": dict(sorted(counts.items())),
        "coverage": coverage,
    }
