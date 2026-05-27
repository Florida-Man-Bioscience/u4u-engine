"""
engine/annotators/cache.py
===========================
Shared SQLite-backed cache for all external API annotator results.

Stores API responses as JSON keyed by (source, lookup_key) so that
repeated queries for the same gene variant skip the network call entirely.

The cache database persists across sessions in DATA_DIR/annotation_cache.db.

Usage
-----
    from .cache import annotation_cache

    # In any annotator:
    cached = annotation_cache.get("vep", "1:12345:A:T")
    if cached is not _MISS:
        return cached

    result = _actual_api_call(...)
    annotation_cache.put("vep", "1:12345:A:T", result)
    return result
"""

import json
import os
import sqlite3
import threading

_CACHE_DB_PATH = os.path.join(os.getenv("DATA_DIR", "data"), "annotation_cache.db")

# Sentinel to distinguish "not in cache" from "cached None"
_MISS = object()


class AnnotationCache:
    """Thread-safe SQLite cache for annotation API results."""

    def __init__(self, db_path: str = _CACHE_DB_PATH):
        self._db_path = db_path
        self._local = threading.local()

    def _conn(self) -> sqlite3.Connection:
        """Get or create a per-thread connection."""
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS annotation_cache (
                    source     TEXT NOT NULL,
                    lookup_key TEXT NOT NULL,
                    result_json TEXT,
                    PRIMARY KEY (source, lookup_key)
                )
            """)
            self._local.conn = conn
        return conn

    def get(self, source: str, lookup_key: str):
        """
        Look up a cached result.

        Returns the deserialized result (which may be None if None was cached),
        or the _MISS sentinel if no cache entry exists.
        """
        conn = self._conn()
        row = conn.execute(
            "SELECT result_json FROM annotation_cache WHERE source = ? AND lookup_key = ?",
            (source, lookup_key),
        ).fetchone()
        if row is None:
            return _MISS
        return json.loads(row[0])

    def put(self, source: str, lookup_key: str, result) -> None:
        """Store a result in the cache (including None results)."""
        conn = self._conn()
        conn.execute(
            "INSERT OR REPLACE INTO annotation_cache (source, lookup_key, result_json) VALUES (?, ?, ?)",
            (source, lookup_key, json.dumps(result)),
        )
        conn.commit()


# Module-level singleton
annotation_cache = AnnotationCache()
MISS = _MISS
