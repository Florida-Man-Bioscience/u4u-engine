# tests/test_engine/test_users/test_oidc_settings.py
from engine.users import oidc


def test_settings_none_when_unconfigured(monkeypatch):
    for k in ("U4U_OIDC_ISSUER", "U4U_OIDC_AUDIENCE", "U4U_OIDC_JWKS_URL"):
        monkeypatch.delenv(k, raising=False)
    assert oidc.oidc_settings() is None


def test_settings_populated_when_all_env_present(monkeypatch):
    monkeypatch.setenv("U4U_OIDC_ISSUER", "https://id.example/app")
    monkeypatch.setenv("U4U_OIDC_AUDIENCE", "u4u-web")
    monkeypatch.setenv("U4U_OIDC_JWKS_URL", "https://id.example/app/jwks")
    s = oidc.oidc_settings()
    assert s is not None
    assert s.issuer == "https://id.example/app"
    assert s.audience == "u4u-web"
    assert s.jwks_url == "https://id.example/app/jwks"


def test_settings_none_when_partial(monkeypatch):
    monkeypatch.setenv("U4U_OIDC_ISSUER", "https://id.example/app")
    monkeypatch.delenv("U4U_OIDC_AUDIENCE", raising=False)
    monkeypatch.setenv("U4U_OIDC_JWKS_URL", "https://id.example/app/jwks")
    assert oidc.oidc_settings() is None
