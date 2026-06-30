"""
engine/users/api.py
====================
FastAPI router for app user accounts.

The endpoints assume the deploy has an Authentik forward-auth proxy in
front: every request that reaches us already carries trusted
``X-Authentik-*`` headers identifying who the human caller is. The
router materialises a local users row on first sight and otherwise
just returns the current row.

Mount in api.py via:
    from engine.users.api import router as users_router
    app.include_router(users_router)
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from . import service
from .db import get_conn

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def get_me(request: Request) -> dict[str, Any]:
    """Return (and lazily create) the user row for the Authentik
    subject on this request.

    Returns 401 when the proxy hasn't forwarded a subject id —
    typically because the request bypassed Authentik or the deploy is
    in open-demo mode without a proxy. The frontend should treat that
    as 'unauthenticated' rather than retrying.
    """
    with get_conn() as conn:
        user = service.upsert_from_headers(conn, request.headers)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="no authenticated user — Authentik headers missing",
        )
    return user.to_dict()


@router.get("")
def list_users() -> list[dict[str, Any]]:
    """List all known users. Intended for admin/operator views; the
    Authentik proxy in front decides who can hit this in production."""
    with get_conn() as conn:
        return [u.to_dict() for u in service.list_users(conn)]
