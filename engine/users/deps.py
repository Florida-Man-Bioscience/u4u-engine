"""
engine/users/deps.py
=====================
FastAPI dependencies that resolve the current end-user to a local
``users`` row via a validated OIDC Bearer access token.

Two flavors:

* ``current_user`` — soft. Returns ``None`` when unauthenticated so
  data-creation endpoints keep working without a token (the resulting
  row is written with ``created_by_user_id = NULL`` instead of
  401-ing the request). A malformed/expired/bad-signature token is
  treated the same as "no token" — silently anonymous — so a garbage
  Authorization header can never turn a soft endpoint into a 500. A
  JWKS outage is different: it means we *can't tell* whether the
  token is valid, so it fails closed by propagating
  ``JwksUnavailable`` rather than silently downgrading to anonymous.

* ``required_user`` — hard. Raises 401 when no authenticated subject
  is present (missing bearer, or a bearer that fails validation), and
  503 when the JWKS endpoint used to validate it is unreachable (fail
  closed rather than either accepting an unverifiable token or
  treating IdP downtime as "no user").

Dev / test mode (no ``U4U_OIDC_*`` env configured — see
``engine.users.oidc.oidc_settings``): both dependencies return a fixed,
stable dev user instead of doing any token work at all. The dev user is
upserted via ``service.upsert_from_token`` with issuer/sub
``"dev-bypass"``, so its ``(issuer, authentik_uid)`` composite key
resolves to the SAME local row across calls/requests — real id, real
FK target, no token required.

The dependencies open a short-lived users-DB connection per request via
``engine.users.db.get_conn``.
"""
from __future__ import annotations

from fastapi import HTTPException, Request

from . import oidc, service
from .db import get_conn
from .models import User
from .token_validator import JwksUnavailable, TokenError, validate_token

DEV_BYPASS_SUB = "dev-bypass"
_DEV_ISSUER = "dev-bypass"


def _bearer(request: Request) -> str | None:
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    return None


def current_user(request: Request) -> User | None:
    """Soft dependency.

    Dev-bypass mode (no OIDC issuer configured) always returns the
    fixed dev user. In OIDC mode: no bearer token -> None; a token that
    fails validation (``TokenError``) -> None, treated as anonymous
    rather than an error, since this is the soft dependency and a
    garbage header must not crash the endpoint; a JWKS outage
    (``JwksUnavailable``) propagates unchanged -- we genuinely don't
    know if the token is good, so we fail closed instead of silently
    downgrading to anonymous.
    """
    settings = oidc.oidc_settings()
    with get_conn() as conn:
        if settings is None:
            # Dev / test: no IdP configured -- inject a stable dev user.
            return service.upsert_from_token(
                conn, issuer=_DEV_ISSUER,
                claims={"sub": DEV_BYPASS_SUB, "preferred_username": "dev"},
            )
        token = _bearer(request)
        if token is None:
            return None
        try:
            claims = validate_token(token, settings)
        except TokenError:
            return None
        return service.upsert_from_token(conn, issuer=settings.issuer, claims=claims)


def required_user(request: Request) -> User:
    """Hard dependency: 401 when unauthenticated, 503 when the JWKS
    endpoint needed to validate the token is unreachable."""
    try:
        user = current_user(request)
    except JwksUnavailable:
        raise HTTPException(status_code=503, detail="identity provider unavailable")
    except TokenError:
        raise HTTPException(status_code=401, detail="invalid access token")
    if user is None:
        raise HTTPException(status_code=401, detail="authentication required")
    return user
