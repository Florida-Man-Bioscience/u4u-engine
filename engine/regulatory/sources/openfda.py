"""
openFDA client — drug enforcement (recalls) and adverse-event counts per peptide.

API key (OPENFDA_API_KEY) is optional but raises rate limits.
"""

from __future__ import annotations

import os

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from ._base import cached_fetch

_SOURCE = "openfda"
_TTL = 60 * 60 * 24
_TIMEOUT = 10
_ENFORCEMENT = "https://api.fda.gov/drug/enforcement.json"
_EVENT = "https://api.fda.gov/drug/event.json"


def _params(search_term: str, limit: int = 5) -> dict:
    p = {"search": search_term, "limit": limit}
    key = os.getenv("OPENFDA_API_KEY")
    if key:
        p["api_key"] = key
    return p


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def _query(url: str, params: dict) -> dict:
    res = requests.get(url, params=params, timeout=_TIMEOUT)
    if res.status_code == 404:
        # openFDA returns 404 for zero-result queries; treat as empty
        return {"results": [], "meta": {"results": {"total": 0}}}
    res.raise_for_status()
    return res.json()


def _fetch(search_term: str) -> dict:
    # Recalls / warning letters via enforcement endpoint
    enforcement_query = f'product_description:"{search_term}"'
    enforcement = _query(_ENFORCEMENT, _params(enforcement_query))
    recalls = [
        {
            "recall_number": r.get("recall_number"),
            "reason": r.get("reason_for_recall"),
            "status": r.get("status"),
            "classification": r.get("classification"),
            "report_date": r.get("report_date"),
            "product_description": r.get("product_description"),
        }
        for r in enforcement.get("results", []) or []
    ]
    recalls_total = ((enforcement.get("meta") or {}).get("results") or {}).get("total", len(recalls))

    # Adverse-event signal — just totals, not per-event details (too noisy).
    try:
        events_query = f'patient.drug.medicinalproduct:"{search_term}"'
        events = _query(_EVENT, _params(events_query, limit=1))
        events_total = ((events.get("meta") or {}).get("results") or {}).get("total", 0)
    except Exception:
        events_total = None

    return {
        "search_term": search_term,
        "recalls_total": recalls_total,
        "recalls": recalls,
        "adverse_events_total": events_total,
    }


def fetch_openfda(search_term: str) -> dict:
    return cached_fetch(_SOURCE, search_term, _TTL, lambda: _fetch(search_term))
