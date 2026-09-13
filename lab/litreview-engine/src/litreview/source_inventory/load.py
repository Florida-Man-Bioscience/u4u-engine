"""Load inventory JSONL bundles. Does not open PDFs or URLs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BUNDLE_FILES = (
    "source_manifest.jsonl",
    "page_receipts.jsonl",
    "contexts.jsonl",
    "units.jsonl",
    "dispositions.jsonl",
    "scope_policy.jsonl",
    "span_links.jsonl",
    "source_qa.jsonl",
)

SCHEMA = "source-inventory-v1"


def load_jsonl(path: Path) -> list[tuple[int, dict[str, Any]]]:
    """Return (1-based line number, object) for non-blank lines."""
    out: list[tuple[int, dict[str, Any]]] = []
    if not path.is_file():
        return out
    for i, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        out.append((i, json.loads(line)))
    return out


def load_bundle(bundle_dir: Path) -> dict[str, list[tuple[int, dict[str, Any]]]]:
    root = Path(bundle_dir)
    return {name: load_jsonl(root / name) for name in BUNDLE_FILES}
