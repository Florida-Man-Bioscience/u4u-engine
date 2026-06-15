"""
engine/annotators/cache.py
===========================
Shared cache for all external API annotator results.

In production (DATABASE_URL set), results are stored in Postgres using a
per-thread connection from the shared pool. In local dev / tests (no
DATABASE_URL, or an explicit db_path is supplied), falls back to an
in-process SQLite file — the same behavior as before.

Gracefully degrades: if neither Postgres nor SQLite is reachable, the cache
is silently bypassed and all calls go directly to the API.
"""

import json
import logging
import os
import threading

log = logging.getLogger(__name__)

_CACHE_DB_PATH = os.path.join(os.getenv("DATA_DIR", "data"), "annotation_cache.db")

# Sentinel to distinguish "not in cache" from "cached None"
_MISS = object()


class AnnotationCache:
    """
    Thread-safe cache for annotation API results.

    When `db_path` is None and DATABASE_URL is set, connects to Postgres.
    When `db_path` is explicitly provided (or DATABASE_URL is absent),
    uses a thread-local SQLite connection at that path.
    """

    def __init__(self, db_path: str | None = None):
        from db.pool import DATABASE_URL

        # Use Postgres when no explicit path is given and DATABASE_URL is set.
        self._use_pg = (db_path is None) and bool(DATABASE_URL)
        self._db_path = db_path if not self._use_pg else None
        self._local = threading.local()

    # ── Postgres path ──────────────────────────────────────────────────────────

    def _pg_conn(self):
        """Per-thread wrapped psycopg2 connection from the shared pool.

        Checked out once per thread and reused for the lifetime of that thread
        (typically a single pipeline execution in the ThreadPoolExecutor).
        """
        wrapper = getattr(self._local, "pg_conn", None)
        if wrapper is not None and not wrapper.closed:
            return wrapper
        if getattr(self._local, "pg_failed", False):
            return None
        try:
            from db.pool import get_raw_conn
            wrapper = get_raw_conn()  # returns _ConnWrapper
            self._local.pg_conn = wrapper
            return wrapper
        except Exception as exc:
            log.warning(
                "Annotation cache Postgres unavailable: %s — falling back to API calls", exc
            )
            self._local.pg_failed = True
            return None

    def _pg_put(self, conn) -> None:
        """Commit the current transaction on the thread-local Postgres conn."""
        try:
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass

    # ── SQLite path ────────────────────────────────────────────────────────────

    def _sqlite_conn(self):
        import sqlite3
        conn = getattr(self._local, "sqlite_conn", None)
        if conn is not None:
            return conn
        if getattr(self._local, "sqlite_failed", False):
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
            self._local.sqlite_conn = conn
            return conn
        except Exception as exc:
            log.warning("Annotation cache unavailable (%s): %s — falling back to API calls", self._db_path, exc)
            self._local.sqlite_failed = True
            return None

    # ── Public API ─────────────────────────────────────────────────────────────

    def get(self, source: str, lookup_key: str):
        """
        Look up a cached result.

        Returns the deserialized result (which may be None if None was cached),
        or the _MISS sentinel if no entry exists or the cache is unavailable.
        """
        if self._use_pg:
            conn = self._pg_conn()
            if conn is None:
                return _MISS
            try:
                row = conn.execute(
                    "SELECT result_json FROM annotation_cache WHERE source = %s AND lookup_key = %s",
                    (source, lookup_key),
                ).fetchone()
                if row is None:
                    return _MISS
                return json.loads(row["result_json"] if isinstance(row, dict) else row[0])
            except Exception:
                return _MISS
        else:
            conn = self._sqlite_conn()
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
        """Store a result. Silently skips if the cache is unavailable."""
        if self._use_pg:
            conn = self._pg_conn()
            if conn is None:
                return
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO annotation_cache (source, lookup_key, result_json)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (source, lookup_key) DO UPDATE
                        SET result_json = EXCLUDED.result_json
                    """,
                    (source, lookup_key, json.dumps(result)),
                )
                self._pg_put(conn)
            except Exception:
                pass
        else:
            conn = self._sqlite_conn()
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


# Module-level singleton — uses Postgres when DATABASE_URL is set
annotation_cache = AnnotationCache()
MISS = _MISS
