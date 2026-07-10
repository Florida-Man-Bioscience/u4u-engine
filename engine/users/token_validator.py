"""
engine/users/token_validator.py
===============================
Stateless validation of end-user OIDC access tokens against the
dedicated Authentik's JWKS. No server-side session — every request is
authenticated by verifying the Bearer token's signature and claims.
"""
from __future__ import annotations

import threading

import jwt

from .oidc import OidcSettings


class TokenError(Exception):
    """Token missing/expired/wrong-claims/bad-signature — maps to 401."""


class JwksUnavailable(Exception):
    """JWKS endpoint unreachable — maps to 503 (fail closed)."""


_clients: dict[str, "jwt.PyJWKClient"] = {}
_clients_lock = threading.Lock()


def _client_for(jwks_url: str) -> "jwt.PyJWKClient":
    with _clients_lock:
        client = _clients.get(jwks_url)
        if client is None:
            client = jwt.PyJWKClient(jwks_url, cache_keys=True)
            _clients[jwks_url] = client
        return client


def _signing_key_for(token: str, jwks_url: str):
    """Resolve the signing key for a token via JWKS. Isolated so tests
    can monkeypatch it without touching the network."""
    try:
        return _client_for(jwks_url).get_signing_key_from_jwt(token)
    except jwt.PyJWKClientError as exc:  # includes network/JWKS fetch errors
        raise JwksUnavailable(str(exc)) from exc


def validate_token(token: str, settings: OidcSettings) -> dict:
    signing_key = _signing_key_for(token, settings.jwks_url)
    try:
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.audience,
            issuer=settings.issuer,
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc
