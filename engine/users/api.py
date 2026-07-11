"""
engine/users/api.py
====================
FastAPI router for app user accounts.

``/users/me`` identifies the caller via a validated OIDC Bearer access
token (see ``engine.users.deps.required_user``) — the end-user IdP is
distinct from the cluster-admin Authentik forward-auth proxy fronting
the deploy. ``GET /users`` is an admin/operator listing gated to
dev-bypass mode or staff (cluster-Authentik) callers — an ordinary
end-user caller must not be able to enumerate every user's PII.

Mount in api.py via:
    from engine.users.api import router as users_router
    app.include_router(users_router)
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from . import oidc, service
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
def list_users(user: User = Depends(required_user)) -> list[dict[str, Any]]:
    """List all known users. Admin/operator view only.

    Allowed in dev-bypass mode (no ``U4U_OIDC_*`` configured -- local
    dev/demo) or when the caller is authenticated via the cluster-admin
    (staff) Authentik issuer. An OIDC-mode caller authenticated via the
    dedicated end-user IdP gets 403 -- this endpoint returns every
    user's username/email and must not be reachable by an ordinary end
    user. Mirrors the dev-bypass-or-authorized pattern used by
    ``POST /tracking/seed``.
    """
    if oidc.oidc_settings() is not None:
        staff_issuer = oidc.cluster_issuer() or "cluster-authentik"
        if user.issuer != staff_issuer:
            raise HTTPException(status_code=403, detail="staff access required")
    with get_conn() as conn:
        return [u.to_dict() for u in service.list_users(conn)]
