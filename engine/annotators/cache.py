"""
engine/annotators/cache.py
===========================
Shared SQLite-backed cache for all external API annotator results.

Stores API responses as JSON keyed by (source, lookup_key) so that
repeated queries for the same gene variant skip the network call entirely.

The cache database persists across sessions in DATA_DIR/annotation_cache.db.

Gracefully degrades: if the database is unwritable (e.g. Docker volume
permissions), the cache is silently bypassed and all calls go to the API.
"""

import json
import logging
import os
import sqlite3
import threading

log = logging.getLogger(__name__)

_CACHE_DB_PATH = os.path.join(os.getenv("DATA_DIR", "data"), "annotation_cache.db")

# Sentinel to distinguish "not in cache" from "cached None"
_MISS = object()


class AnnotationCache:
    """Thread-safe SQLite cache for annotation API results."""

    def __init__(self, db_path: str = _CACHE_DB_PATH):
        self._db_path = db_path
        self._local = threading.local()

    def _conn(self) -> sqlite3.Connection | None:
        """Get or create a per-thread connection. Returns None if DB is unavailable."""
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            return conn

        # Mark as attempted so we don't retry on every call
        if getattr(self._local, "failed", False):
            return None

        try:
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
        except Exception as exc:
            log.warning("Annotation cache unavailable (%s): %s — falling back to API calls", self._db_path, exc)
            self._local.failed = True
            return None

    def get(self, source: str, lookup_key: str):
        """
        Look up a cached result.

        Returns the deserialized result (which may be None if None was cached),
        or the _MISS sentinel if no cache entry exists or the DB is unavailable.
        """
        conn = self._conn()
        if conn is None:
            return _MISS
        try:
            row = conn.execute(
                "SELECT result_json FROM annotation_cache WHERE source = ? AND lookup_key = ?",
                (source, lookup_key),
            ).fetchone()
            if row is None:
                return _MISS
            return json.loads(row[0])
        except Exception:
            return _MISS

    def put(self, source: str, lookup_key: str, result) -> None:
        """Store a result in the cache. Silently skips if DB is unavailable."""
        conn = self._conn()
        if conn is None:
            return
        try:
            conn.execute(
                "INSERT OR REPLACE INTO annotation_cache (source, lookup_key, result_json) VALUES (?, ?, ?)",
                (source, lookup_key, json.dumps(result)),
            )
            conn.commit()
        except Exception:
            pass


# Module-level singleton
annotation_cache = AnnotationCache()
MISS = _MISS
