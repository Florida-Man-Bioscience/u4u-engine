"""CLI helpers for inventory validate / coverage report."""

from __future__ import annotations

import json
from pathlib import Path

from litreview.source_inventory.coverage import coverage_report
from litreview.source_inventory.validate import validate_inventory


def dumps(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def run_validate(bundle: Path, ledger: Path | None, allow_fixture_qa: bool) -> tuple[int, str]:
    result = validate_inventory(bundle, ledger_path=ledger, allow_fixture_qa=allow_fixture_qa)
    code = 0 if result["valid"] else 1
    return code, dumps(result)


def run_coverage(
    bundle: Path,
    ledger: Path | None,
    allow_fixture_qa: bool,
    require: str | None,
) -> tuple[int, str]:
    report = coverage_report(bundle, ledger_path=ledger, allow_fixture_qa=allow_fixture_qa)
    text = dumps(report)
    if not report["validation"]["valid"]:
        return 1, text
    if require:
        g = report["gates"].get(require.replace("-", "_"))
        if not g or not g["pass"]:
            return 1, text
    return 0, text
