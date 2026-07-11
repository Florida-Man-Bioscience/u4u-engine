"""
engine/users/oidc.py
====================
Environment-driven OIDC settings for end-user access-token validation.

When the three U4U_OIDC_* vars are all present the app runs in
authenticated mode (production). When they are absent, oidc_settings()
returns None and the auth dependencies fall back to the dev-bypass user
(local dev / tests).
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class OidcSettings:
    issuer: str
    audience: str
    jwks_url: str


def oidc_settings() -> OidcSettings | None:
    issuer = (os.getenv("U4U_OIDC_ISSUER") or "").strip()
    audience = (os.getenv("U4U_OIDC_AUDIENCE") or "").strip()
    jwks_url = (os.getenv("U4U_OIDC_JWKS_URL") or "").strip()
    if issuer and audience and jwks_url:
        return OidcSettings(issuer=issuer, audience=audience, jwks_url=jwks_url)
    return None


def cluster_issuer() -> str | None:
    return (os.getenv("U4U_CLUSTER_AUTHENTIK_ISSUER") or "").strip() or None


_OIDC_VARS = ("U4U_OIDC_ISSUER", "U4U_OIDC_AUDIENCE", "U4U_OIDC_JWKS_URL")


def resolve_auth_mode() -> str:
    """Resolve and validate the boot-time auth mode from ``U4U_OIDC_*``.

    Returns ``"oidc"`` when all three vars are set, ``"dev-bypass"``
    when none are set. Raises ``RuntimeError`` when only SOME are set
    -- a partial config must never silently fall through to
    dev-bypass, which would collapse every caller onto one shared dev
    user (a silent IDOR reopen). The error message names the missing
    var(s) so a misconfigured deploy is diagnosable from the boot log
    alone.

    Called once at FastAPI startup (see api.py's lifespan) so a
    misconfigured prod deploy refuses to boot instead of running with
    auth effectively disabled.
    """
    present = {v: bool((os.getenv(v) or "").strip()) for v in _OIDC_VARS}
    if all(present.values()):
        return "oidc"
    if not any(present.values()):
        return "dev-bypass"
    missing = [v for v, ok in present.items() if not ok]
    raise RuntimeError(
        "Partial U4U_OIDC_* configuration detected -- refusing to boot. "
        f"Missing: {', '.join(missing)}. Set all three of {', '.join(_OIDC_VARS)} "
        "to run in OIDC mode, or none of them to run in dev-bypass mode."
    )
