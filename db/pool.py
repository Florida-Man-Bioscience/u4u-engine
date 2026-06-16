"""
db/pool.py
==========
Shared psycopg2 connection pool for all Postgres database access.

Provides a _ConnWrapper that adds sqlite3-compatible conn.execute() shortcut
to psycopg2 connections, so service/analysis code works identically against
both Postgres (production) and SQLite (local dev / tests).

Thread-safe; suitable for FastAPI sync handlers and ThreadPoolExecutor.
"""

import logging
import os
import threading
from contextlib import contextmanager
from typing import Generator

import psycopg2
import psycopg2.extras
import psycopg2.pool

log = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "")

_POOL_MIN = 2
_POOL_MAX = 25

_pool: psycopg2.pool.ThreadedConnectionPool | None = None
_pool_lock = threading.Lock()


class _ConnWrapper:
    """
    Wraps a psycopg2 connection to expose a sqlite3-compatible execute() shortcut.

    sqlite3 connections have conn.execute(sql, params) as a convenience method
    that creates a cursor, executes, and returns it.  psycopg2 connections do
    not. This wrapper adds that method so service/analysis SQL code is
    database-agnostic.
    """

    _is_pg = True  # checked by _ph() in service.py

    def __init__(self, conn: psycopg2.extensions.connection) -> None:
        self._conn = conn

    def execute(self, sql: str, params=None):
        """Create a cursor, execute sql, and return the cursor."""
        cur = self._conn.cursor()
        if params is None:
            cur.execute(sql)
        else:
            cur.execute(sql, params)
        return cur

    def cursor(self):
        return self._conn.cursor()

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    @property
    def closed(self) -> int:
        return self._conn.closed


def _get_pool() -> psycopg2.pool.ThreadedConnectionPool | None:
    global _pool
    if _pool is not None:
        return _pool
    if not DATABASE_URL:
        return None
    with _pool_lock:
        if _pool is None:
            try:
                _pool = psycopg2.pool.ThreadedConnectionPool(
                    _POOL_MIN, _POOL_MAX, dsn=DATABASE_URL
                )
                log.info(
                    "Postgres connection pool initialized (min=%d, max=%d)",
                    _POOL_MIN, _POOL_MAX,
                )
            except Exception:
                log.exception("Failed to create Postgres connection pool")
    return _pool


def is_configured() -> bool:
    """Return True when DATABASE_URL is set (Postgres mode)."""
    return bool(DATABASE_URL)


@contextmanager
def get_conn() -> Generator[_ConnWrapper, None, None]:
    """
    Context manager that yields a wrapped psycopg2 connection from the pool.

    The wrapper adds sqlite3-compatible execute() so service code is
    database-agnostic. Commits on clean exit, rolls back on exception,
    and always returns the connection to the pool.

    Usage::

        with get_conn() as conn:
            row = conn.execute("SELECT 1").fetchone()
    """
    pool = _get_pool()
    if pool is None:
        raise RuntimeError(
            "DATABASE_URL is not set — Postgres connection unavailable."
        )
    raw = pool.getconn()
    raw.cursor_factory = psycopg2.extras.RealDictCursor
    conn = _ConnWrapper(raw)
    try:
        yield conn
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        pool.putconn(raw)


def get_raw_conn(*, autocommit: bool = False) -> _ConnWrapper:
    """
    Check out a wrapped connection from the pool without a context manager.

    Pass autocommit=True for long-lived thread-local handles (e.g. the
    annotation cache) where holding an implicit transaction across many
    reads would block writers on row locks. Per-statement commit is fine
    when each call is a single INSERT … ON CONFLICT or a single SELECT.

    The caller MUST call `put_conn(conn)` when done.
    Prefer `get_conn()` context manager whenever possible.
    """
    pool = _get_pool()
    if pool is None:
        raise RuntimeError("DATABASE_URL is not set")
    raw = pool.getconn()
    raw.cursor_factory = psycopg2.extras.RealDictCursor
    raw.autocommit = autocommit
    return _ConnWrapper(raw)


def put_conn(conn: _ConnWrapper) -> None:
    """Return a connection obtained via `get_raw_conn()` to the pool."""
    pool = _get_pool()
    if pool is not None:
        pool.putconn(conn._conn)
