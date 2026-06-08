"""
engine/regulatory/aggregator.py
================================
Merges curated peptide JSON with live source results into the payload
served by /regulatory/peptides and /regulatory/events.

Live source failures are tolerated — the curated layer always renders;
the per-source `status` field tells the frontend whether each augment is
fresh, stale, or unavailable.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from .sources import (
    fetch_docket_summary,
    fetch_federal_register,
    fetch_openfda,
    fetch_trials,
)
from .store import engine_covered_slugs, load_events, load_peptides

log = logging.getLogger(__name__)


def _live_for_peptide(peptide: dict, executor: ThreadPoolExecutor) -> dict:
    """Run the 3 per-peptide live sources in parallel."""
    tasks: dict[str, Callable[[], dict]] = {
        "clinicaltrials": lambda: fetch_trials(peptide["clinicaltrials_search_term"]),
        "openfda": lambda: fetch_openfda(peptide["openfda_search_term"]),
        "federal_register": lambda: fetch_federal_register(peptide["federal_register_search_term"]),
    }
    futures = {executor.submit(fn): name for name, fn in tasks.items()}
    out: dict[str, dict] = {}
    for fut in as_completed(futures):
        name = futures[fut]
        try:
            out[name] = fut.result()
        except Exception as exc:
            log.warning("source %s failed for %s: %s", name, peptide["slug"], exc)
            out[name] = {"data": None, "fetched_at": None, "status": "unavailable", "source": name}
    return out


def _summary_stats(peptides: list[dict]) -> dict:
    """Compute the top-of-page KPI numbers from curated categorizations."""
    by_cat: dict[str, int] = {}
    by_wave: dict[str, int] = {}
    for p in peptides:
        by_cat[p["category"]] = by_cat.get(p["category"], 0) + 1
        wave = p.get("pcac_wave")
        if wave:
            by_wave[wave] = by_wave.get(wave, 0) + 1
    return {
        "by_category": by_cat,
        "by_pcac_wave": by_wave,
        "total_peptides": len(peptides),
    }


def build_dashboard_payload(include_live: bool = True, max_workers: int = 6) -> dict:
    """
    Build the full /regulatory/peptides response.

    Set include_live=False to return only curated data (used in tests, or
    when serving an SSR placeholder before live data hydrates).
    """
    data = load_peptides()
    peptides = data["peptides"]
    categories = data["categories"]
    engine_slugs = engine_covered_slugs()

    enriched: list[dict] = []
    if include_live:
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            for p in peptides:
                live = _live_for_peptide(p, ex)
                enriched.append({**p, "engine_covered": p["slug"] in engine_slugs, "live": live})
    else:
        for p in peptides:
            enriched.append({**p, "engine_covered": p["slug"] in engine_slugs, "live": {}})

    return {
        "categories": categories,
        "peptides": enriched,
        "stats": _summary_stats(peptides),
        "last_curated": data.get("last_curated"),
    }


def build_events_payload(include_live: bool = True) -> dict:
    """
    Build /regulatory/events response — curated events + sources + the
    docket comments augment.
    """
    data = load_events()
    docket_id = data.get("regulations_gov_docket_id")
    docket_live = None
    if include_live and docket_id:
        try:
            docket_live = fetch_docket_summary(docket_id)
        except Exception as exc:
            log.warning("docket fetch failed: %s", exc)
            docket_live = {"data": None, "fetched_at": None, "status": "unavailable", "source": "regulations_gov"}
    return {
        "events": data["events"],
        "official_sources": data["official_sources"],
        "pcac_contact": data.get("pcac_contact"),
        "regulations_gov_docket_id": docket_id,
        "docket_live": docket_live,
        "last_curated": data.get("last_curated"),
    }
