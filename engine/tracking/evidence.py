"""
engine/tracking/evidence.py
===========================
Research-backed evidence registry for peptide -> biomarker response.

The magnitudes in :mod:`engine.tracking.biomarker_params` are informal —
"sourced informally from the biomarker panel literature; not a tight
clinical claim." This module layers a *curated, citation-anchored* registry
on top of them so that:

  1. Every effect magnitude we lean on can be traced to a real, retrieved
     paper (DOI), with an explicit evidence GRADE.
  2. The Bayesian prior's uncertainty scales with that grade: a marker
     backed by human RCTs gets a tighter ``relative_sd`` than the flat
     ``PANEL_REL_SD = 0.20`` default; a preclinical-only marker gets a
     wider one. See :func:`relative_sd_for`, consumed by
     :func:`engine.tracking.genetics.derive_prior`.
  3. The registry is *updatable from research without code changes* — it
     lives in ``data/biomarker_evidence.json`` and is edited through the
     curator CLI :mod:`engine.tracking.evidence_update`.

Honesty contract
----------------
An entry exists only when a curator has recorded at least one citation they
actually retrieved (e.g. via the scite literature tools). Markers without
an entry are *uncited* — :func:`relative_sd_for` returns ``None`` for them
and the prior falls back to the legacy ``PANEL_REL_SD``. Uncited is the
truth for most of the panel today; the registry never invents provenance to
fill the gap.

No third-party dependencies — stdlib ``json`` only.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

# Default registry location. DATA_DIR mirrors the rest of the engine so a
# deployment can relocate it; tests pass an explicit path.
_DEFAULT_PATH = Path(os.getenv("DATA_DIR", "data")) / "biomarker_evidence.json"

_VALID_GRADES = {"A", "B", "C", "D"}

# Fallback relative_sd by grade when an entry omits an explicit value.
# Mirrors ``grade_default_relative_sd`` in the JSON; duplicated here so the
# loader is self-sufficient if the JSON omits the block.
_GRADE_DEFAULT_SD: dict[str, float] = {"A": 0.10, "B": 0.15, "C": 0.22, "D": 0.30}


class EvidenceError(ValueError):
    """Raised when the evidence registry fails validation."""


@dataclass(frozen=True)
class Citation:
    doi: str
    title: str
    authors: str
    year: int
    journal: str
    design: str            # e.g. "RCT", "Review", "Animal/in vitro"
    evidence: str          # "human" | "preclinical"

    def to_dict(self) -> dict[str, Any]:
        return {
            "doi": self.doi,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "journal": self.journal,
            "design": self.design,
            "evidence": self.evidence,
            "url": f"https://doi.org/{self.doi}",
        }


@dataclass(frozen=True)
class Evidence:
    """One curated, cited biomarker-response parameter set."""
    biomarker: str
    max_pct_change: float
    relative_sd: float
    grade: str
    peptides: tuple[str, ...]
    rationale: str
    citations: tuple[Citation, ...]
    last_reviewed: str     # ISO date

    def to_dict(self) -> dict[str, Any]:
        return {
            "biomarker": self.biomarker,
            "max_pct_change": self.max_pct_change,
            "relative_sd": self.relative_sd,
            "grade": self.grade,
            "peptides": list(self.peptides),
            "rationale": self.rationale,
            "citations": [c.to_dict() for c in self.citations],
            "last_reviewed": self.last_reviewed,
            "n_citations": len(self.citations),
        }


# ── Loading & validation ────────────────────────────────────────────────────

# Process-wide cache keyed by resolved path. Cleared by reset_cache() in tests.
_cache: dict[str, dict[str, Evidence]] = {}


def _coerce_citation(raw: dict[str, Any], *, biomarker: str) -> Citation:
    doi = str(raw.get("doi", "")).strip()
    if not doi:
        raise EvidenceError(f"{biomarker}: a citation is missing its DOI")
    try:
        year = int(raw["year"])
    except (KeyError, TypeError, ValueError) as exc:
        raise EvidenceError(f"{biomarker}: citation {doi} has an invalid year") from exc
    return Citation(
        doi=doi,
        title=str(raw.get("title", "")).strip(),
        authors=str(raw.get("authors", "")).strip(),
        year=year,
        journal=str(raw.get("journal", "")).strip(),
        design=str(raw.get("design", "")).strip(),
        evidence=str(raw.get("evidence", "")).strip(),
    )


def _coerce_entry(biomarker: str, raw: dict[str, Any]) -> Evidence:
    grade = str(raw.get("grade", "")).strip().upper()
    if grade not in _VALID_GRADES:
        raise EvidenceError(
            f"{biomarker}: grade {grade!r} not in {sorted(_VALID_GRADES)}"
        )

    citations_raw = raw.get("citations") or []
    if not citations_raw:
        raise EvidenceError(
            f"{biomarker}: an evidence entry must have >=1 citation "
            f"(honesty contract — uncited markers belong in BIOMARKER_PARAMS, "
            f"not here)"
        )
    citations = tuple(_coerce_citation(c, biomarker=biomarker) for c in citations_raw)

    # relative_sd: explicit value wins; else grade default.
    rel_sd = raw.get("relative_sd")
    if rel_sd is None:
        rel_sd = _GRADE_DEFAULT_SD[grade]
    rel_sd = float(rel_sd)
    if not (0.0 < rel_sd <= 1.0):
        raise EvidenceError(
            f"{biomarker}: relative_sd {rel_sd} must be in (0, 1]"
        )

    try:
        max_pct = float(raw["max_pct_change"])
    except (KeyError, TypeError, ValueError) as exc:
        raise EvidenceError(f"{biomarker}: missing/invalid max_pct_change") from exc

    last_reviewed = str(raw.get("last_reviewed", "")).strip()
    try:
        date.fromisoformat(last_reviewed)
    except ValueError as exc:
        raise EvidenceError(
            f"{biomarker}: last_reviewed {last_reviewed!r} is not an ISO date"
        ) from exc

    peptides = tuple(str(p).strip() for p in (raw.get("peptides") or ()) if str(p).strip())

    return Evidence(
        biomarker=biomarker,
        max_pct_change=max_pct,
        relative_sd=rel_sd,
        grade=grade,
        peptides=peptides,
        rationale=str(raw.get("rationale", "")).strip(),
        citations=citations,
        last_reviewed=last_reviewed,
    )


def _load_uncached(path: Path) -> dict[str, Evidence]:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if not isinstance(doc, dict):
        raise EvidenceError(f"{path}: top-level JSON must be an object")
    entries = doc.get("entries") or {}
    if not isinstance(entries, dict):
        raise EvidenceError(f"{path}: 'entries' must be an object")
    out: dict[str, Evidence] = {}
    for biomarker, raw in entries.items():
        out[biomarker] = _coerce_entry(biomarker, raw)
    return out


def load_evidence(path: str | os.PathLike | None = None) -> dict[str, Evidence]:
    """Load (and cache) the evidence registry keyed by biomarker name.

    Returns an empty dict when the registry file is absent — the engine is
    fully functional without it (every marker is simply uncited). Raises
    :class:`EvidenceError` on a malformed registry so a curation mistake
    fails loudly rather than silently degrading every prior.
    """
    p = Path(path) if path is not None else _DEFAULT_PATH
    key = str(p.resolve()) if p.exists() else str(p)
    if key not in _cache:
        _cache[key] = _load_uncached(p)
    return _cache[key]


def reset_cache() -> None:
    """Test helper — drop the in-process registry cache."""
    _cache.clear()


# ── Lookups consumed by the prior layer ─────────────────────────────────────

def evidence_for(biomarker_name: str,
                 *, path: str | os.PathLike | None = None) -> Evidence | None:
    """Return the curated evidence for one biomarker, or None if uncited."""
    return load_evidence(path).get((biomarker_name or "").strip())


def relative_sd_for(biomarker_name: str,
                    *, path: str | os.PathLike | None = None) -> float | None:
    """Evidence-derived relative SD for a biomarker's effect magnitude.

    Returns ``None`` when the marker has no evidence entry — the caller
    (``genetics.derive_prior``) then falls back to the legacy
    ``PANEL_REL_SD``. This keeps uncited markers — most of the panel —
    behaving exactly as before.
    """
    ev = evidence_for(biomarker_name, path=path)
    return ev.relative_sd if ev is not None else None


def grade_default_sd(grade: str) -> float:
    """Default relative_sd for an evidence grade (A/B/C/D)."""
    return _GRADE_DEFAULT_SD[grade.strip().upper()]
