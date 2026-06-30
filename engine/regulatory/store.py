"""
engine/regulatory/store.py
==========================
Loads curated regulatory data from data/regulatory/*.json and exposes the
canonical peptide list (union of dashboard medspa peptides + engine
PEPTIDE_GENE_MAP entries).
"""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path

_DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
_PEPTIDES_PATH = _DATA_DIR / "regulatory" / "peptides.json"
_EVENTS_PATH = _DATA_DIR / "regulatory" / "events.json"


def _normalize(name: str) -> str:
    """Lowercase + strip non-alphanumerics, for fuzzy peptide-name matching."""
    return re.sub(r"[^a-z0-9]+", "", name.lower())


@lru_cache(maxsize=1)
def load_peptides() -> dict:
    """Return the parsed peptides.json contents."""
    with open(_PEPTIDES_PATH, encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def load_events() -> dict:
    """Return the parsed events.json contents."""
    with open(_EVENTS_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def get_peptide(slug: str) -> dict | None:
    for p in load_peptides()["peptides"]:
        if p["slug"] == slug:
            return p
    return None


def engine_peptide_names() -> set[str]:
    """Normalized names from PEPTIDE_GENE_MAP — for cross-referencing."""
    from engine.annotators.peptide_mapper import PEPTIDE_GENE_MAP

    names: set[str] = set()
    for combo in PEPTIDE_GENE_MAP.keys():
        for piece in re.split(r"\s*\+\s*", combo):
            names.add(_normalize(piece))
    return names


def engine_covered_slugs() -> set[str]:
    """
    Slugs whose peptide name (or alias) is also analyzed by the engine.

    Used by the frontend to show a 'your engine scores this' chip on
    peptide cards.
    """
    engine_names = engine_peptide_names()
    covered: set[str] = set()
    for p in load_peptides()["peptides"]:
        candidates = [p["name"]] + p.get("aliases", [])
        if any(_normalize(c) in engine_names for c in candidates):
            covered.add(p["slug"])
    return covered


def reset_cache() -> None:
    """Test helper — drop the lru_cache so re-reading the JSON files works."""
    load_peptides.cache_clear()
    load_events.cache_clear()
