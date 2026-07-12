# tests/test_engine/test_users/test_deps_auth.py
import pytest
from fastapi import HTTPException
from starlette.requests import Request

from engine.users import deps
from engine.users.token_validator import JwksUnavailable, TokenError


def _req(headers=None):
    raw = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    return Request({"type": "http", "headers": raw})


def test_dev_bypass_returns_fixed_user_when_unconfigured(monkeypatch):
    monkeypatch.setattr(deps.oidc, "oidc_settings", lambda: None)
    u = deps.required_user(_req())
    assert u is not None
    assert u.authentik_uid == deps.DEV_BYPASS_SUB
    # stable identity across calls
    assert deps.required_user(_req()).id == u.id


def test_missing_bearer_is_401_in_oidc_mode(monkeypatch):
    monkeypatch.setattr(deps.oidc, "oidc_settings", lambda: _FAKE_SETTINGS)
    with pytest.raises(HTTPException) as ei:
        deps.required_user(_req())
    assert ei.value.status_code == 401


def test_invalid_token_is_401(monkeypatch):
    monkeypatch.setattr(deps.oidc, "oidc_settings", lambda: _FAKE_SETTINGS)
    monkeypatch.setattr(deps, "validate_token",
                        lambda t, s: (_ for _ in ()).throw(TokenError("bad")))
    with pytest.raises(HTTPException) as ei:
        deps.required_user(_req({"Authorization": "Bearer x"}))
    assert ei.value.status_code == 401


def test_jwks_unavailable_is_503(monkeypatch):
    monkeypatch.setattr(deps.oidc, "oidc_settings", lambda: _FAKE_SETTINGS)
    monkeypatch.setattr(deps, "validate_token",
                        lambda t, s: (_ for _ in ()).throw(JwksUnavailable("down")))
    with pytest.raises(HTTPException) as ei:
        deps.required_user(_req({"Authorization": "Bearer x"}))
    assert ei.value.status_code == 503


def test_valid_token_upserts_and_returns_user(monkeypatch):
    monkeypatch.setattr(deps.oidc, "oidc_settings", lambda: _FAKE_SETTINGS)
    monkeypatch.setattr(deps, "validate_token",
                        lambda t, s: {"sub": "u1", "email": "u1@x.co"})
    u = deps.required_user(_req({"Authorization": "Bearer good"}))
    assert u.authentik_uid == "u1"
    assert u.issuer == _FAKE_SETTINGS.issuer


from engine.users.oidc import OidcSettings  # noqa: E402

_FAKE_SETTINGS = OidcSettings(issuer="https://id.example/app",
                              audience="u4u-web",
                              jwks_url="https://id.example/app/jwks")
