"""
Federal Register API client — most recent notices mentioning a peptide.

No auth required.
"""

from __future__ import annotations

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from ._base import cached_fetch

_SOURCE = "federal_register"
_TTL = 60 * 60 * 6  # 6 hours
_TIMEOUT = 6
_BASE = "https://www.federalregister.gov/api/v1/documents.json"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def _query(search_term: str) -> dict:
    res = requests.get(
        _BASE,
        params={
            "conditions[term]": search_term,
            "conditions[type][]": ["RULE", "PRORULE", "NOTICE"],
            "order": "newest",
            "per_page": 5,
            "fields[]": ["title", "document_number", "publication_date", "html_url", "abstract"],
        },
        timeout=_TIMEOUT,
    )
    res.raise_for_status()
    return res.json()


def _fetch(search_term: str) -> dict:
    payload = _query(search_term)
    results = payload.get("results", []) or []
    return {
        "search_term": search_term,
        "total": payload.get("count", len(results)),
        "documents": [
            {
                "title": d.get("title"),
                "document_number": d.get("document_number"),
                "publication_date": d.get("publication_date"),
                "url": d.get("html_url"),
                "abstract": d.get("abstract"),
            }
            for d in results
        ],
    }


def fetch_federal_register(search_term: str) -> dict:
    return cached_fetch(_SOURCE, search_term, _TTL, lambda: _fetch(search_term))
