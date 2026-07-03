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
DATABASE_URL  async SQLAlchemy URL, e.g.
              postgresql+asyncpg://u4u:u4u@db:5432/u4u
              When empty, health ingestion is disabled (endpoints return 503).
"""
from __future__ import annotations

import os
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

def _normalize_url(url: str) -> str:
    """Coerce a standard Postgres URL into an asyncpg SQLAlchemy URL.

    Managed hosts (Render, Heroku, Fly) hand out ``postgres://`` or
    ``postgresql://`` URLs, often with a psycopg2-style ``?sslmode=`` param that
    asyncpg rejects. Normalize the driver and drop that param so the same
    DATABASE_URL works locally and in production.
    """
    if not url:
        return url
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and "+asyncpg" not in url.split("://", 1)[0]:
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    # asyncpg uses `ssl`, not libpq's `sslmode` — strip it if present.
    if "sslmode=" in url:
        base, _, query = url.partition("?")
        kept = "&".join(p for p in query.split("&") if not p.startswith("sslmode="))
        url = base + (f"?{kept}" if kept else "")
    return url


DATABASE_URL = _normalize_url(os.getenv("DATABASE_URL", "").strip())
HEALTH_DB_ENABLED = bool(DATABASE_URL)

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def _init() -> None:
    """Create the engine + session factory once, on first use."""
    global _engine, _sessionmaker
    if not HEALTH_DB_ENABLED or _engine is not None:
        return
    _engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
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
    db/migrations/004_health_ingestion.sql via psql and treat this as a no-op.
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
