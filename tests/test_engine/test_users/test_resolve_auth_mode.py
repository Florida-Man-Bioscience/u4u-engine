# tests/test_engine/test_users/test_resolve_auth_mode.py
"""
FIX 1 (whole-branch review): a prod deploy that sets 2-of-3 U4U_OIDC_*
vars must fail LOUD at boot instead of silently falling open to
dev-bypass (which collapses every caller onto one shared dev user —
a silent IDOR reopen). See engine.users.oidc.resolve_auth_mode.
"""
import pytest

from engine.users import oidc

_ALL_VARS = ("U4U_OIDC_ISSUER", "U4U_OIDC_AUDIENCE", "U4U_OIDC_JWKS_URL")


def _clear(monkeypatch):
    for k in _ALL_VARS:
        monkeypatch.delenv(k, raising=False)


def test_resolve_auth_mode_oidc_when_all_set(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("U4U_OIDC_ISSUER", "https://id.example/app")
    monkeypatch.setenv("U4U_OIDC_AUDIENCE", "u4u-web")
    monkeypatch.setenv("U4U_OIDC_JWKS_URL", "https://id.example/app/jwks")
    assert oidc.resolve_auth_mode() == "oidc"


def test_resolve_auth_mode_dev_bypass_when_none_set(monkeypatch):
    _clear(monkeypatch)
    assert oidc.resolve_auth_mode() == "dev-bypass"


@pytest.mark.parametrize(
    "present",
    [
        ("U4U_OIDC_ISSUER",),
        ("U4U_OIDC_AUDIENCE",),
        ("U4U_OIDC_JWKS_URL",),
        ("U4U_OIDC_ISSUER", "U4U_OIDC_AUDIENCE"),
        ("U4U_OIDC_ISSUER", "U4U_OIDC_JWKS_URL"),
        ("U4U_OIDC_AUDIENCE", "U4U_OIDC_JWKS_URL"),
    ],
)
def test_resolve_auth_mode_raises_on_partial_config(monkeypatch, present):
    _clear(monkeypatch)
    for k in present:
        monkeypatch.setenv(k, "x")
    with pytest.raises(RuntimeError) as ei:
        oidc.resolve_auth_mode()
    missing = [v for v in _ALL_VARS if v not in present]
    for m in missing:
        assert m in str(ei.value)
