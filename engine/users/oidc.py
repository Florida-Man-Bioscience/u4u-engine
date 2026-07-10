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
