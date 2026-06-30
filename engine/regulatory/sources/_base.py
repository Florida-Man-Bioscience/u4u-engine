"""Shared cache+TTL helper for live regulatory sources."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

from ..cache import MISS, regulatory_cache

log = logging.getLogger(__name__)

T = TypeVar("T")


def cached_fetch(
    source: str,
    lookup_key: str,
    ttl_seconds: int,
    fetch_fn: Callable[[], T | None],
) -> dict:
    """
    Wrap a source-specific fetch with TTL caching + stale fallback.

    Returns a dict with the standard envelope:
      {
        "data": <result or None>,
        "fetched_at": <epoch float>,
        "status": "fresh" | "stale" | "unavailable",
        "source": <source>,
      }

    On fetch failure, returns the most recent stale value if one exists,
    flagged as "stale". If no value has ever been cached, status is
    "unavailable" with data=None.
    """
    hit, fetched_at = regulatory_cache.get(source, lookup_key, ttl_seconds)
    if hit is not MISS:
        return {
            "data": hit,
            "fetched_at": fetched_at,
            "status": "fresh",
            "source": source,
        }

    try:
        value = fetch_fn()
        fetched_at = regulatory_cache.put(source, lookup_key, value)
        return {
            "data": value,
            "fetched_at": fetched_at,
            "status": "fresh",
            "source": source,
        }
    except Exception as exc:
        log.warning("Live fetch failed for %s/%s: %s", source, lookup_key, exc)
        stale_value, stale_at = regulatory_cache.get_stale(source, lookup_key)
        if stale_value is not MISS:
            return {
                "data": stale_value,
                "fetched_at": stale_at,
                "status": "stale",
                "source": source,
            }
        return {
            "data": None,
            "fetched_at": time.time(),
            "status": "unavailable",
            "source": source,
        }
