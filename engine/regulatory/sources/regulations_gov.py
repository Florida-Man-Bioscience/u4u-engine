"""
Regulations.gov v4 client — comment counts for FDA docket FDA-2025-N-6895.

Requires REGULATIONS_GOV_API_KEY (free, signup at api.data.gov). Without
the key the source is unavailable; the dashboard still renders with a
"unavailable" badge on this section.
"""

from __future__ import annotations

import os

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from ._base import cached_fetch

_SOURCE = "regulations_gov"
_TTL = 60 * 60  # 1 hour
_TIMEOUT = 10
_BASE = "https://api.regulations.gov/v4"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def _query_comments(docket_id: str, api_key: str) -> dict:
    res = requests.get(
        f"{_BASE}/comments",
        params={
            "filter[docketId]": docket_id,
            "page[size]": 5,
            "sort": "-postedDate",
        },
        headers={"X-Api-Key": api_key},
        timeout=_TIMEOUT,
    )
    res.raise_for_status()
    return res.json()


def _fetch(docket_id: str) -> dict | None:
    api_key = os.getenv("REGULATIONS_GOV_API_KEY")
    if not api_key:
        return None
    payload = _query_comments(docket_id, api_key)
    meta = payload.get("meta") or {}
    data = payload.get("data") or []
    latest = data[0]["attributes"] if data else None
    return {
        "docket_id": docket_id,
        "comments_count": meta.get("totalElements"),
        "last_comment_posted_at": latest.get("postedDate") if latest else None,
        "docket_url": f"https://www.regulations.gov/docket/{docket_id}",
    }


def fetch_docket_summary(docket_id: str) -> dict:
    return cached_fetch(_SOURCE, docket_id, _TTL, lambda: _fetch(docket_id))
