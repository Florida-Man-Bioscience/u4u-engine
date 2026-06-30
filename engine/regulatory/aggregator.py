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
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from .sources import (
    fetch_docket_summary,
    fetch_federal_register,
    fetch_openfda,
    fetch_trials,
)
from .store import engine_covered_slugs, load_events, load_peptides

log = logging.getLogger(__name__)


_SOURCE_FETCHERS: dict[str, tuple[str, Callable[[str], dict]]] = {
    "clinicaltrials": ("clinicaltrials_search_term", fetch_trials),
    "openfda": ("openfda_search_term", fetch_openfda),
    "federal_register": ("federal_register_search_term", fetch_federal_register),
}


def _fan_out_live(peptides: list[dict], max_workers: int) -> dict[str, dict[str, dict]]:
    """
    Run every (peptide × source) live fetch in a single executor.

    A nested per-peptide ThreadPoolExecutor would serialise across peptides
    (one batch of 3 in flight at a time). Flattening means the dashboard's
    cold-cache latency is roughly one upstream round-trip, not N of them.
    """
    out: dict[str, dict[str, dict]] = {p["slug"]: {} for p in peptides}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures: dict = {}
        for p in peptides:
            for name, (term_key, fetch_fn) in _SOURCE_FETCHERS.items():
                fut = ex.submit(fetch_fn, p[term_key])
                futures[fut] = (p["slug"], name)
        for fut in as_completed(futures):
            slug, name = futures[fut]
            try:
                out[slug][name] = fut.result()
            except Exception as exc:
                log.warning("source %s failed for %s: %s", name, slug, exc)
                out[slug][name] = {
                    "data": None,
                    "fetched_at": None,
                    "status": "unavailable",
                    "source": name,
                }
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


def build_dashboard_payload(include_live: bool = True, max_workers: int = 12) -> dict:
    """
    Build the full /regulatory/peptides response.

    Set include_live=False to return only curated data — used by the SSR
    initial render so the dashboard paints from cached JSON without
    blocking on any upstream calls.
    """
    data = load_peptides()
    peptides = data["peptides"]
    categories = data["categories"]
    engine_slugs = engine_covered_slugs()

    live_by_slug: dict[str, dict[str, dict]] = (
        _fan_out_live(peptides, max_workers) if include_live else {}
    )

    enriched = [
        {
            **p,
            "engine_covered": p["slug"] in engine_slugs,
            "live": live_by_slug.get(p["slug"], {}),
        }
        for p in peptides
    ]

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
