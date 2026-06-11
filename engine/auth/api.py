"""
engine/auth/api.py
==================
FastAPI router for username/password auth.

Endpoints
---------
- POST /auth/login   — {username, password} → {token, expires_at, user}
- POST /auth/logout  — invalidate the caller's session token (requires auth)
- GET  /auth/me      — return the current user (requires auth)

``/auth/login`` is intentionally exempted from the global auth middleware
in ``api.py`` so a fresh client can obtain a token. ``/auth/logout`` and
``/auth/me`` are NOT exempted — they require a valid session token (or
API key) like any other protected endpoint, and read the calling user
out of ``request.state.auth_user`` set by the middleware.
"""
from __future__ import annotations

import logging
import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from . import service
from .db import get_conn
from .rate_limit import login_limiter


log = logging.getLogger("u4u.auth")


router = APIRouter(prefix="/auth", tags=["auth"])


# Test-injection hook, mirrors the pattern in engine/tracking/api.py.
_override_conn: sqlite3.Connection | None = None


def _conn() -> sqlite3.Connection:
    if _override_conn is not None:
        return _override_conn
    return get_conn()


def set_test_conn(conn: sqlite3.Connection | None) -> None:
    global _override_conn
    _override_conn = conn


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=256)


@router.post("/login")
def login(body: LoginIn, request: Request) -> dict[str, Any]:
    """Exchange username+password for an opaque session token.

    Returns 401 on bad credentials, 429 when the per-IP rate limit has
    been exceeded. The middleware in ``api.py`` exempts this endpoint so
    unauthenticated clients can reach it.
    """
    key = _client_key(request)
    if not login_limiter.check(key):
        retry_after = login_limiter.retry_after_seconds(key)
        log.warning("auth: login rate limit exceeded for %s", key)
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Try again later.",
            headers={"Retry-After": str(int(retry_after) + 1)},
        )

    # Record every attempt — including successful ones — so a brute-forcer
    # who happens to get a correct answer mid-window doesn't reset the
    # budget for their next batch of attempts.
    try:
        user = service.authenticate(
            _conn(), username=body.username, password=body.password,
        )
    except service.AuthError:
        login_limiter.record(key)
        log.info("auth: failed login for username=%r from %s", body.username, key)
        raise HTTPException(status_code=401, detail="invalid credentials")

    login_limiter.record(key)
    session = service.create_session(_conn(), user_id=user.id)
    log.info("auth: login success user=%s from %s", user.username, key)
    return {
        "token": session.token,
        "expires_at": session.expires_at,
        "user": user.to_dict(),
    }


@router.post("/logout")
def logout(request: Request) -> dict[str, Any]:
    """Invalidate the bearer token used to make this call.

    Idempotent: returns ``{"revoked": false}`` if the token wasn't a
    session token (e.g. when calling with an API key) or had already
    been revoked.
    """
    token = _bearer_token(request)
    revoked = service.revoke_session(_conn(), token) if token else False
    return {"revoked": revoked}


@router.get("/me")
def me(request: Request) -> dict[str, Any]:
    """Return the calling user when authenticated via session token.

    With an API key (service-to-service), no user is associated, so we
    return a sentinel payload rather than 404 — useful for clients that
    just want to test their credentials.
    """
    user = getattr(request.state, "auth_user", None)
    if user is None:
        return {"user": None, "via": "api_key"}
    return {"user": user.to_dict(), "via": "session"}


def _bearer_token(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return ""


def _client_key(request: Request) -> str:
    """Return the rate-limit key for a request.

    Honours the first entry of ``X-Forwarded-For`` when present (Caddy in
    front of the API populates it). Falls back to the direct socket peer.
    The header is unauthenticated input, but the only way to abuse it is
    to spread your own attempts across spoofed prefixes — which doesn't
    let you bypass another user's quota, it just gives YOU more budget,
    which a real attacker already has via a botnet anyway. The point of
    this limiter is to slow casual brute-forcers, not to defeat a
    well-resourced one.
    """
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    client = request.client
    return client.host if client else "unknown"
