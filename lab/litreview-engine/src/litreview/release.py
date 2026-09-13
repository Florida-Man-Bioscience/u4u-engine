"""Release gates for a demo corpus. Bookkeeping, not semantic truth."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from litreview.claim_test import validate_claim_test
from litreview.validate import validate_batch


def release_check(
    records: list[dict[str, Any]],
    claim_tests: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    errors = validate_batch(records)
    props = [r for r in records if r.get("kind") == "proposition"]
    links = [r for r in records if r.get("kind") == "evidence_link"]
    ct_err = []
    for s in claim_tests or []:
        ct_err.extend(validate_claim_test(s))
    ok = not errors and not ct_err and bool(props)
    return {
        "pass": ok,
        "n_records": len(records),
        "n_propositions": len(props),
        "n_evidence_links": len(links),
        "validate_errors": errors[:20],
        "claim_test_errors": ct_err,
        "notes": [
            "pass means deterministic admission + claim-test shape",
            "not verified-on-data",
            "not all-facts-extracted",
        ],
    }


def write_report(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
