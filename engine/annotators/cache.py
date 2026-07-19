"""
engine/annotators/cache.py
===========================
Shared cache for all external API annotator results.

In production (DATABASE_URL set), results are stored in Postgres, borrowing a
connection from the shared pool per operation and always returning it (holding
one per thread leaked the pool — see ``_pg_conn``). In local dev / tests (no
DATABASE_URL, or an explicit db_path is supplied), falls back to an
in-process SQLite file — the same behavior as before.

Gracefully degrades: if neither Postgres nor SQLite is reachable, the cache
is silently bypassed and all calls go directly to the API.
"""

import json
import logging
import os
import threading
from contextlib import contextmanager

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

    @contextmanager
    def _pg_conn(self):
        """Borrow a pooled connection for ONE cache operation, always returning it.

        This used to check a connection out per thread and stash it in
        thread-local state for the lifetime of that thread — but nothing ever
        called ``put_conn``, so every worker thread that touched the cache
        permanently consumed one of the pool's connections. The pipeline
        annotates on 8 threads per job, so the pool drained over hours and then
        every DB-backed request failed with
        ``psycopg2.pool.PoolError: connection pool exhausted`` — taking down
        tracking, users and jobs while ``/health`` stayed green.

        Pool checkout is a cheap in-process operation, so borrowing per call is
        the right trade for guaranteed release. Autocommit so a read doesn't
        leave an idle transaction sitting on locks — each statement is atomic.

        Yields ``None`` (rather than raising) when Postgres is unavailable, so
        the cache degrades to live API calls instead of breaking the pipeline.
        """
        if getattr(self._local, "pg_failed", False):
            yield None
            return
        try:
            from db.pool import get_raw_conn, put_conn
            wrapper = get_raw_conn(autocommit=True)
        except Exception as exc:
            log.warning(
                "Annotation cache Postgres unavailable: %s — falling back to API calls", exc
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
                log.warning("Failed returning annotation-cache connection to the pool",
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
            conn = sqlite3.connect(self._db_path, timeout=10.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS annotation_cache (
                    source     TEXT NOT NULL,
                    lookup_key TEXT NOT NULL,
                    result_json TEXT,
                    fetched_at REAL NOT NULL DEFAULT 0,
                    PRIMARY KEY (source, lookup_key)
                )
            """)
            # SQLite has no ADD COLUMN IF NOT EXISTS; probe PRAGMA so
            # pre-existing dev DBs gain fetched_at without manual cleanup.
            cols = {row[1] for row in conn.execute("PRAGMA table_info(annotation_cache)").fetchall()}
            if "fetched_at" not in cols:
                conn.execute("ALTER TABLE annotation_cache ADD COLUMN fetched_at REAL NOT NULL DEFAULT 0")
                conn.commit()
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
            with self._pg_conn() as conn:
                if conn is None:
                    return _MISS
                try:
                    row = conn.execute(
                        "SELECT result_json FROM annotation_cache "
                        "WHERE source = %s AND lookup_key = %s",
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
        """Store a result. Silently skips if the cache is unavailable.

        Also evicts entries older than 90 days on the same call. Upstream
        (ClinVar / gnomAD / dbSNP) refreshes monthly, so 90 days covers
        two cycles; the per-table index on fetched_at makes the DELETE
        a cheap no-op when nothing has aged out.
        """
        if self._use_pg:
            with self._pg_conn() as conn:
                if conn is None:
                    return
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "DELETE FROM annotation_cache "
                        "WHERE fetched_at < NOW() - INTERVAL '90 days'"
                    )
                    cur.execute(
                        """
                        INSERT INTO annotation_cache
                            (source, lookup_key, result_json, fetched_at)
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT (source, lookup_key) DO UPDATE
                            SET result_json = EXCLUDED.result_json,
                                fetched_at  = EXCLUDED.fetched_at
                        """,
                        (source, lookup_key, json.dumps(result)),
                    )
                except Exception:
                    pass
        else:
            conn = self._sqlite_conn()
            if conn is None:
                return
            try:
                import time
                cutoff = time.time() - 90 * 86400
                conn.execute(
                    "DELETE FROM annotation_cache WHERE fetched_at < ?",
                    (cutoff,),
                )
                conn.execute(
                    "INSERT OR REPLACE INTO annotation_cache "
                    "(source, lookup_key, result_json, fetched_at) "
                    "VALUES (?, ?, ?, ?)",
                    (source, lookup_key, json.dumps(result), time.time()),
                )
                conn.commit()
            except Exception:
                pass


# Module-level singleton — uses Postgres when DATABASE_URL is set
annotation_cache = AnnotationCache()
MISS = _MISS
