"""
engine/health/db.py
===================
Async SQLAlchemy 2.0 session layer for the HealthKit datastore.

This is the engine's first real Postgres connection (the genomics job store is
in-memory + encrypted-file; biomarker tracking is SQLite). It is intentionally
self-contained and lazy: nothing connects until a request needs a session, and
the whole feature no-ops when DATABASE_URL is unset.

Environment
-----------
DATABASE_URL  Postgres URL shared with the rest of the engine. The canonical
              form is the SYNC (psycopg2) URL the migrations + connection pool
              use, e.g. postgresql://u4u:pw@host:5432/u4u?sslmode=disable. This
              module derives an async (asyncpg) URL from it — swapping the driver
              and dropping libpq-only query params (sslmode, …) — so a single
              DATABASE_URL drives both the sync stack and this async datastore
              against one Postgres. An already-async URL is accepted unchanged.
              When empty, health ingestion is disabled (endpoints return 503).
"""
from __future__ import annotations

import os
from collections.abc import AsyncIterator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# libpq/psycopg2 query params that asyncpg's connection URL does not accept.
_DROP_QUERY_KEYS = {"sslmode", "channel_binding", "gssencmode", "target_session_attrs"}


def _to_async_url(raw: str) -> str:
    """Derive an asyncpg SQLAlchemy URL from the (usually sync) DATABASE_URL.

    Swaps any postgres driver to ``postgresql+asyncpg`` and strips libpq-only
    query params (e.g. ``sslmode``) that asyncpg rejects. Idempotent on a URL
    that is already ``postgresql+asyncpg://``.
    """
    parts = urlsplit(raw)
    scheme = parts.scheme
    if scheme in ("postgres", "postgresql") or scheme.startswith("postgresql+"):
        scheme = "postgresql+asyncpg"
    query = urlencode(
        [
            (k, v)
            for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if k.lower() not in _DROP_QUERY_KEYS
        ]
    )
    return urlunsplit((scheme, parts.netloc, parts.path, query, parts.fragment))


DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
HEALTH_DB_ENABLED = bool(DATABASE_URL)
ASYNC_DATABASE_URL = _to_async_url(DATABASE_URL) if DATABASE_URL else ""

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def _init() -> None:
    """Create the engine + session factory once, on first use."""
    global _engine, _sessionmaker
    if not HEALTH_DB_ENABLED or _engine is not None:
        return
    _engine = create_async_engine(ASYNC_DATABASE_URL, pool_pre_ping=True)
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)


def session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the session factory (raises if the datastore is disabled)."""
    _init()
    if _sessionmaker is None:
        raise RuntimeError("Health datastore is disabled (set DATABASE_URL).")
    return _sessionmaker


async def init_models() -> None:
    """Create tables if they don't exist. Called from the API lifespan.

    Idempotent and safe to run every boot; for production, prefer applying
    db/migrations/008_healthkit_ingestion.sql via psql and treat this as a no-op.
    """
    _init()
    if _engine is None:
        return
    from engine.health.models import Base

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a request-scoped AsyncSession."""
    from fastapi import HTTPException

    _init()
    if _sessionmaker is None:
        raise HTTPException(
            status_code=503,
            detail="Health datastore not configured (set DATABASE_URL).",
        )
    async with _sessionmaker() as session:
        yield session


async def dispose() -> None:
    """Dispose the engine on shutdown (clean test teardown / graceful restart)."""
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _sessionmaker = None
