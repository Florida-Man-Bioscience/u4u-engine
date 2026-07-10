"""
engine/users/api.py
====================
FastAPI router for app user accounts.

``/users/me`` identifies the caller via a validated OIDC Bearer access
token (see ``engine.users.deps.required_user``) — the end-user IdP is
distinct from the cluster-admin Authentik forward-auth proxy fronting
the deploy. ``GET /users`` remains an admin/operator listing; the
forward-auth proxy in front decides who can reach it.

Mount in api.py via:
    from engine.users.api import router as users_router
    app.include_router(users_router)
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from . import service
from .db import get_conn
from .deps import required_user
from .models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def get_me(user: User = Depends(required_user)) -> dict[str, Any]:
    """Return the user row for the current request's authenticated
    subject (OIDC Bearer token, or the dev-bypass user when no OIDC
    issuer is configured).

    401 when unauthenticated (missing/invalid Bearer token in OIDC
    mode); 503 when the identity provider's JWKS endpoint is
    unreachable. See ``engine.users.deps.required_user``.
    """
    return user.to_dict()


@router.get("")
def list_users() -> list[dict[str, Any]]:
    """List all known users. Intended for admin/operator views; the
    Authentik proxy in front decides who can hit this in production."""
    with get_conn() as conn:
        return [u.to_dict() for u in service.list_users(conn)]
