"""
engine/regulatory/cache.py
==========================
TTL-aware cache for live regulatory source results.

Two backends, picked once per cache instance:
  * Postgres ``regulatory_cache`` (migration 006) when DATABASE_URL is
    set and no explicit ``db_path`` was passed.
  * SQLite at ``data/regulatory_cache.db`` (its own file — not the
    annotation cache's DB) otherwise. Tests construct the cache with an
    explicit tmp path to keep runs isolated.

The wire-level shape of ``fetched_at`` is epoch seconds (float) in both
backends so the frontend's ``new Date(fetched_at * 1000)`` keeps working
without a code change. In PG the column is TIMESTAMPTZ; SELECTs pull
``EXTRACT(EPOCH FROM fetched_at)`` to keep the contract consistent.

Falls back silently to a cache miss if neither backend is reachable, so
a misconfigured DB doesn't turn a degraded dashboard into a 500.
"""

import json
import logging
import os
import threading
import time
from contextlib import contextmanager

log = logging.getLogger(__name__)

_DEFAULT_SQLITE_PATH = os.path.join(os.getenv("DATA_DIR", "data"), "regulatory_cache.db")

_MISS = object()


class RegulatoryCache:
    """Thread-safe TTL cache backed by Postgres or SQLite."""

    def __init__(self, db_path: str | None = None):
        from db.pool import DATABASE_URL

        # Use Postgres when no explicit path is given and DATABASE_URL is set.
        # An explicit db_path always forces SQLite (tests + dev overrides).
        self._use_pg = (db_path is None) and bool(DATABASE_URL)
        self._db_path = db_path if not self._use_pg else None
        if not self._use_pg and self._db_path is None:
            self._db_path = _DEFAULT_SQLITE_PATH
        self._local = threading.local()

    # ── Postgres path ──────────────────────────────────────────────────────────

    @contextmanager
    def _pg_conn(self):
        """Borrow a pooled connection for ONE cache operation, always returning it.

        This previously cached a connection per thread and never called
        ``put_conn``, leaking a pool slot per worker thread until the pool
        drained (``PoolError: connection pool exhausted``) and every DB-backed
        endpoint 500'd. autocommit keeps each SELECT/INSERT atomic so reads
        don't hold an idle transaction that blocks writers.

        Yields ``None`` when Postgres is unavailable so callers bypass the cache.
        """
        if getattr(self._local, "pg_failed", False):
            yield None
            return
        try:
            from db.pool import get_raw_conn, put_conn
            wrapper = get_raw_conn(autocommit=True)
        except Exception as exc:
            log.warning(
                "Regulatory cache Postgres unavailable: %s — bypassing cache", exc
            )
            self._local.pg_failed = True
            yield None
            return
        try:
            yield wrapper
        finally:
            try:
                put_conn(wrapper)
            except Exception:
                log.warning("Failed returning regulatory-cache connection to the pool",
                            exc_info=True)

    # ── SQLite path ────────────────────────────────────────────────────────────

    def _sqlite_conn(self):
        import sqlite3
        conn = getattr(self._local, "sqlite_conn", None)
        if conn is not None:
            return conn
        if getattr(self._local, "sqlite_failed", False):
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
            self._local.sqlite_conn = conn
            return conn
        except Exception as exc:
            log.warning(
                "Regulatory cache unavailable (%s): %s — bypassing cache",
                self._db_path, exc,
            )
            self._local.sqlite_failed = True
            return None

    # ── Public API ─────────────────────────────────────────────────────────────

    def get(self, source: str, lookup_key: str, ttl_seconds: int):
        """Look up a cached result, honoring TTL.

        Returns ``(value, fetched_at_epoch)`` on hit (value may be None
        if None was cached). Returns ``(_MISS, fetched_at_or_None)`` on
        miss or expiry — the second element carries the stale timestamp
        so callers can render a "last attempt" age even when the entry
        is too old to use.
        """
        if self._use_pg:
            with self._pg_conn() as conn:
                if conn is None:
                    return _MISS, None
                try:
                    row = conn.execute(
                        """
                        SELECT result_json,
                               EXTRACT(EPOCH FROM fetched_at) AS fetched_at_epoch
                        FROM regulatory_cache
                        WHERE source = %s AND lookup_key = %s
                        """,
                        (source, lookup_key),
                    ).fetchone()
                    if row is None:
                        return _MISS, None
                    result_json = row["result_json"] if isinstance(row, dict) else row[0]
                    fetched_at = float(
                        row["fetched_at_epoch"] if isinstance(row, dict) else row[1]
                    )
                    if time.time() - fetched_at > ttl_seconds:
                        return _MISS, fetched_at
                    return json.loads(result_json), fetched_at
                except Exception:
                    return _MISS, None
        else:
            conn = self._sqlite_conn()
            if conn is None:
                return _MISS, None
            try:
                row = conn.execute(
                    "SELECT result_json, fetched_at FROM regulatory_cache "
                    "WHERE source = ? AND lookup_key = ?",
                    (source, lookup_key),
                ).fetchone()
                if row is None:
                    return _MISS, None
                result_json, fetched_at = row[0], float(row[1])
                if time.time() - fetched_at > ttl_seconds:
                    return _MISS, fetched_at
                return json.loads(result_json), fetched_at
            except Exception:
                return _MISS, None

    def put(self, source: str, lookup_key: str, result) -> float:
        """Store a result with the current timestamp. Returns the
        fetched_at epoch the caller can echo back to the frontend."""
        now = time.time()
        if self._use_pg:
            with self._pg_conn() as conn:
                if conn is None:
                    return now
                try:
                    conn.execute(
                        """
                        INSERT INTO regulatory_cache
                            (source, lookup_key, result_json, fetched_at)
                        VALUES (%s, %s, %s, to_timestamp(%s))
                        ON CONFLICT (source, lookup_key) DO UPDATE
                            SET result_json = EXCLUDED.result_json,
                                fetched_at  = EXCLUDED.fetched_at
                        """,
                        (source, lookup_key, json.dumps(result), now),
                    )
                except Exception:
                    pass
                return now

        conn = self._sqlite_conn()
        if conn is None:
            return now
        try:
            conn.execute(
                "INSERT OR REPLACE INTO regulatory_cache "
                "(source, lookup_key, result_json, fetched_at) "
                "VALUES (?, ?, ?, ?)",
                (source, lookup_key, json.dumps(result), now),
            )
            conn.commit()
        except Exception:
            pass
        return now

    def get_stale(self, source: str, lookup_key: str):
        """Return the most recently cached value regardless of TTL, for
        use when a live fetch fails and we want to serve last-known data
        with a 'stale' badge. Returns ``(value, fetched_at)`` or
        ``(_MISS, None)`` when nothing was ever cached."""
        if self._use_pg:
            with self._pg_conn() as conn:
                if conn is None:
                    return _MISS, None
                try:
                    row = conn.execute(
                        """
                        SELECT result_json,
                               EXTRACT(EPOCH FROM fetched_at) AS fetched_at_epoch
                        FROM regulatory_cache
                        WHERE source = %s AND lookup_key = %s
                        """,
                        (source, lookup_key),
                    ).fetchone()
                    if row is None:
                        return _MISS, None
                    result_json = row["result_json"] if isinstance(row, dict) else row[0]
                    fetched_at = float(
                        row["fetched_at_epoch"] if isinstance(row, dict) else row[1]
                    )
                    return json.loads(result_json), fetched_at
                except Exception:
                    return _MISS, None

        conn = self._sqlite_conn()
        if conn is None:
            return _MISS, None
        try:
            row = conn.execute(
                "SELECT result_json, fetched_at FROM regulatory_cache "
                "WHERE source = ? AND lookup_key = ?",
                (source, lookup_key),
            ).fetchone()
            if row is None:
                return _MISS, None
            return json.loads(row[0]), float(row[1])
        except Exception:
            return _MISS, None


regulatory_cache = RegulatoryCache()
MISS = _MISS
