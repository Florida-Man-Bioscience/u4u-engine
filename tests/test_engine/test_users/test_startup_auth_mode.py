# tests/test_engine/test_users/test_startup_auth_mode.py
"""
FIX 1: the FastAPI app must refuse to boot when U4U_OIDC_* is
partially configured, instead of silently falling open to dev-bypass.
engine.users.oidc.resolve_auth_mode() is called from api.py's lifespan
startup (near _run_db_migrations()); a RuntimeError there must
propagate and prevent the app from starting.
"""
import pytest
from fastapi.testclient import TestClient

import api

_ALL_VARS = ("U4U_OIDC_ISSUER", "U4U_OIDC_AUDIENCE", "U4U_OIDC_JWKS_URL")


def _clear(monkeypatch):
    for k in _ALL_VARS:
        monkeypatch.delenv(k, raising=False)


def test_app_refuses_to_boot_on_partial_oidc_config(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("U4U_OIDC_ISSUER", "https://id.example/app")
    monkeypatch.setenv("U4U_OIDC_AUDIENCE", "u4u-web")
    # U4U_OIDC_JWKS_URL intentionally left unset.
    with pytest.raises(RuntimeError, match="U4U_OIDC_JWKS_URL"):
        with TestClient(api.app):
            pass
