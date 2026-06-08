"""
engine/regulatory/cache.py
==========================
TTL-aware SQLite cache for live regulatory source results.

Lives in the same DB file as the genomic annotation cache but in its own
table (regulatory_cache) because regulatory data needs TTL semantics while
genomic data does not.
"""

import json
import logging
import os
import sqlite3
import threading
import time

log = logging.getLogger(__name__)

_CACHE_DB_PATH = os.path.join(os.getenv("DATA_DIR", "data"), "annotation_cache.db")

_MISS = object()


class RegulatoryCache:
    """Thread-safe SQLite cache with per-entry TTL."""

    def __init__(self, db_path: str = _CACHE_DB_PATH):
        self._db_path = db_path
        self._local = threading.local()

    def _conn(self) -> sqlite3.Connection | None:
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            return conn
        if getattr(self._local, "failed", False):
            return None
        try:
            os.makedirs(os.path.dirname(self._db_path) or ".", exist_ok=True)
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS regulatory_cache (
                    source      TEXT NOT NULL,
                    lookup_key  TEXT NOT NULL,
                    result_json TEXT,
                    fetched_at  REAL NOT NULL,
                    PRIMARY KEY (source, lookup_key)
                )
            """)
            self._local.conn = conn
            return conn
        except Exception as exc:
            log.warning("Regulatory cache unavailable (%s): %s — falling back to live calls", self._db_path, exc)
            self._local.failed = True
            return None

    def get(self, source: str, lookup_key: str, ttl_seconds: int):
        """
        Look up a cached result, honoring TTL.

        Returns (value, fetched_at_epoch) on hit (value may be None if None
        was cached). Returns (_MISS, None) on miss or when expired.
        """
        conn = self._conn()
        if conn is None:
            return _MISS, None
        try:
            row = conn.execute(
                "SELECT result_json, fetched_at FROM regulatory_cache WHERE source = ? AND lookup_key = ?",
                (source, lookup_key),
            ).fetchone()
            if row is None:
                return _MISS, None
            result_json, fetched_at = row
            if time.time() - fetched_at > ttl_seconds:
                return _MISS, fetched_at
            return json.loads(result_json), fetched_at
        except Exception:
            return _MISS, None

    def put(self, source: str, lookup_key: str, result) -> float:
        """Store a result with current timestamp. Returns fetched_at epoch."""
        now = time.time()
        conn = self._conn()
        if conn is None:
            return now
        try:
            conn.execute(
                "INSERT OR REPLACE INTO regulatory_cache (source, lookup_key, result_json, fetched_at) VALUES (?, ?, ?, ?)",
                (source, lookup_key, json.dumps(result), now),
            )
            conn.commit()
        except Exception:
            pass
        return now

    def get_stale(self, source: str, lookup_key: str):
        """
        Return the most recently cached value regardless of TTL, for use when
        a live fetch fails and we want to serve last-known data with a
        'stale' badge. Returns (value, fetched_at) or (_MISS, None).
        """
        conn = self._conn()
        if conn is None:
            return _MISS, None
        try:
            row = conn.execute(
                "SELECT result_json, fetched_at FROM regulatory_cache WHERE source = ? AND lookup_key = ?",
                (source, lookup_key),
            ).fetchone()
            if row is None:
                return _MISS, None
            return json.loads(row[0]), row[1]
        except Exception:
            return _MISS, None


regulatory_cache = RegulatoryCache()
MISS = _MISS
