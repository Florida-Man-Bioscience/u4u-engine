# End-user auth + access control — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add website end-user identity (dedicated Authentik via stateless OIDC Bearer validation) and resource-level ownership checks that close the IDOR gap, in the FastAPI backend.

**Architecture:** The Next.js SPA obtains an OIDC access token from a dedicated, semi-isolated Authentik (Authorization Code + PKCE) and sends it as `Authorization: Bearer`. FastAPI validates every token against Authentik's JWKS (issuer/audience/expiry/signature), maps the verified `(iss, sub)` to a `users` row, and a reusable ownership guard restricts each resource to `created_by_user_id == user.id`. The `users` table is reused for both staff (cluster Authentik) and end-users, distinguished by an `issuer` column.

**Tech Stack:** Python 3.12, FastAPI, psycopg2 (Postgres) / sqlite3 (dev+tests), `pyjwt[crypto]` + `cryptography` for JWT/JWKS, Nix dev shell, pytest.

## Global Constraints

- Dev shell only: run Python/tests via `nix develop --command ...` (never system Python or `.venv`).
- Dual-dialect SQL: every new query uses the `_ph(conn)` placeholder helper (`%s` Postgres / `?` SQLite) and portable `ON CONFLICT`. Postgres migrations live in `db/migrations/0NN_*.sql`; the SQLite mirror lives in `engine/users/schema.sql` — **keep them in lockstep**.
- Access-control responses: **401** when unauthenticated (prod); **404** on ownership mismatch (never 403 — no existence leak); **503** if JWKS is unreachable (fail closed).
- Dev/test bypass: when no OIDC issuer is configured, inject a fixed dev user so local dev and the existing suite keep working; when an issuer **is** configured, a missing/invalid token is a hard 401.
- End-user rows carry empty `groups`; staff privileges are only granted when `issuer` equals the cluster-Authentik issuer.
- TDD throughout: write the failing test, watch it fail, minimal implementation, watch it pass, commit. Migrations exercised in the Postgres smoke suite (`PG_TESTS=1`).
- Env var names (exact): `U4U_OIDC_ISSUER`, `U4U_OIDC_AUDIENCE`, `U4U_OIDC_JWKS_URL`, `U4U_CLUSTER_AUTHENTIK_ISSUER`, `U4U_AUTH_DEV_USER` (dev-bypass toggle/label).

---

### Task 1: Add JWT/JWKS dependencies

**Files:**
- Modify: `flake.nix:17-43` (withPackages list)
- Modify: `requirements.txt` (Auth section, ~line 31-32)
- Modify: `.github/workflows/test.yml` (both the `test` job pip install ~line 48 and the `postgres-smoke` job pip install)
- Test: `tests/test_engine/test_users/test_oidc_deps.py`

**Interfaces:**
- Produces: `jwt` and `cryptography` importable in the dev shell and CI.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_engine/test_users/test_oidc_deps.py
"""Guard: the JWT/JWKS validation stack must be importable."""


def test_jwt_and_crypto_importable():
    import jwt  # PyJWT
    from cryptography.hazmat.primitives.asymmetric import rsa

    assert hasattr(jwt, "decode")
    assert hasattr(rsa, "generate_private_key")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `nix develop --command python -m pytest tests/test_engine/test_users/test_oidc_deps.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'jwt'`.

- [ ] **Step 3: Add the dependencies**

In `flake.nix`, add to the `python.withPackages` list (after `bcrypt`):

```nix
            # Auth
            bcrypt
            pyjwt
            cryptography
```

In `requirements.txt`, under the Auth section, add:

```
# OIDC access-token validation (end-user auth)
pyjwt[crypto]>=2.8
cryptography>=42.0
```

In `.github/workflows/test.yml`, append `pyjwt[crypto] cryptography` to the `pip install ...` line in **both** the `test` job and the `postgres-smoke` job.

- [ ] **Step 4: Run test to verify it passes**

Run: `nix develop --command python -m pytest tests/test_engine/test_users/test_oidc_deps.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add flake.nix requirements.txt .github/workflows/test.yml tests/test_engine/test_users/test_oidc_deps.py
git commit -m "build(auth): add pyjwt[crypto] + cryptography for OIDC token validation"
```

---

### Task 2: OIDC settings module

**Files:**
- Create: `engine/users/oidc.py`
- Test: `tests/test_engine/test_users/test_oidc_settings.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) class OidcSettings: issuer: str; audience: str; jwks_url: str`
  - `oidc_settings() -> OidcSettings | None` — returns settings when all three env vars are set, else `None` (dev/unconfigured).
  - `cluster_issuer() -> str | None` — value of `U4U_CLUSTER_AUTHENTIK_ISSUER`, or `None`.

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `nix develop --command python -m pytest tests/test_engine/test_users/test_oidc_settings.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.users.oidc'`.

- [ ] **Step 3: Write minimal implementation**

```python
# engine/users/oidc.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `nix develop --command python -m pytest tests/test_engine/test_users/test_oidc_settings.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add engine/users/oidc.py tests/test_engine/test_users/test_oidc_settings.py
git commit -m "feat(auth): env-driven OIDC settings module"
```

---

### Task 3: Access-token validator (JWKS)

**Files:**
- Create: `engine/users/token_validator.py`
- Test: `tests/test_engine/test_users/test_token_validator.py`

**Interfaces:**
- Consumes: `engine.users.oidc.OidcSettings` (Task 2).
- Produces:
  - `class TokenError(Exception)` — invalid token (→ 401 at the dependency).
  - `class JwksUnavailable(Exception)` — JWKS fetch failed (→ 503).
  - `validate_token(token: str, settings: OidcSettings) -> dict` — returns verified claims (`sub`, `iss`, `email`, `name`, …) or raises `TokenError` / `JwksUnavailable`. Uses a module-level `jwt.PyJWKClient` cache keyed by `jwks_url`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_engine/test_users/test_token_validator.py
import time

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from engine.users import token_validator as tv
from engine.users.oidc import OidcSettings

_SETTINGS = OidcSettings(
    issuer="https://id.example/app",
    audience="u4u-web",
    jwks_url="https://id.example/app/jwks",
)


@pytest.fixture
def keypair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key


def _make_token(key, *, iss=_SETTINGS.issuer, aud=_SETTINGS.audience,
                exp_delta=3600, sub="user-123", extra=None, kid="k1"):
    now = 1_800_000_000  # fixed; tests monkeypatch time.time to sit before exp
    payload = {"iss": iss, "aud": aud, "sub": sub,
               "iat": now, "exp": now + exp_delta}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, key, algorithm="RS256", headers={"kid": kid})


def _install_fake_jwks(monkeypatch, key, kid="k1"):
    """Bypass network: feed the validator the public key directly."""
    pub = key.public_key()

    class _FakeSigningKey:
        def __init__(self, k):
            self.key = k

    def _fake_get_key(self, token):  # signature matches PyJWKClient.get_signing_key_from_jwt
        return _FakeSigningKey(pub)

    monkeypatch.setattr(tv, "_signing_key_for", _fake_get_key.__get__(None), raising=True)
    monkeypatch.setattr(time, "time", lambda: 1_800_000_100)


def test_valid_token_returns_claims(monkeypatch, keypair):
    _install_fake_jwks(monkeypatch, keypair)
    token = _make_token(keypair, extra={"email": "a@b.co", "name": "A B"})
    claims = tv.validate_token(token, _SETTINGS)
    assert claims["sub"] == "user-123"
    assert claims["email"] == "a@b.co"


def test_expired_token_rejected(monkeypatch, keypair):
    _install_fake_jwks(monkeypatch, keypair)
    token = _make_token(keypair, exp_delta=-10)
    with pytest.raises(tv.TokenError):
        tv.validate_token(token, _SETTINGS)


def test_wrong_issuer_rejected(monkeypatch, keypair):
    _install_fake_jwks(monkeypatch, keypair)
    token = _make_token(keypair, iss="https://evil.example")
    with pytest.raises(tv.TokenError):
        tv.validate_token(token, _SETTINGS)


def test_wrong_audience_rejected(monkeypatch, keypair):
    _install_fake_jwks(monkeypatch, keypair)
    token = _make_token(keypair, aud="some-other-client")
    with pytest.raises(tv.TokenError):
        tv.validate_token(token, _SETTINGS)


def test_bad_signature_rejected(monkeypatch, keypair):
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    _install_fake_jwks(monkeypatch, keypair)  # validator trusts keypair's pubkey
    token = _make_token(other)                # but token signed by a different key
    with pytest.raises(tv.TokenError):
        tv.validate_token(token, _SETTINGS)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `nix develop --command python -m pytest tests/test_engine/test_users/test_token_validator.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.users.token_validator'`.

- [ ] **Step 3: Write minimal implementation**

```python
# engine/users/token_validator.py
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
    try:
        signing_key = _signing_key_for(token, settings.jwks_url)
    except JwksUnavailable:
        raise
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
```

> **Note for the implementer:** the test monkeypatches `_signing_key_for` to return an object with a `.key` attribute holding the public key, and patches `time.time` so the fixed `exp` is in the future. If the real `PyJWKClient` signature differs in the installed PyJWT version, adjust `_signing_key_for` and the test's patch target together — keep them in lockstep.

- [ ] **Step 4: Run test to verify it passes**

Run: `nix develop --command python -m pytest tests/test_engine/test_users/test_token_validator.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add engine/users/token_validator.py tests/test_engine/test_users/test_token_validator.py
git commit -m "feat(auth): OIDC access-token validator (JWKS, fail-closed)"
```

---

### Task 4: Data model — `issuer` column (migration 012 + model + reads)

**Files:**
- Create: `db/migrations/012_user_issuer.sql`
- Modify: `engine/users/schema.sql` (SQLite mirror)
- Modify: `engine/users/models.py` (add `issuer` field to `User`)
- Modify: `engine/users/service.py` (add `get_user_by_issuer_sub`)
- Test: `tests/test_engine/test_users/test_issuer_model.py`; migration assertion added to `tests/test_postgres_smoke.py`

**Interfaces:**
- Produces:
  - `User.issuer: str` field (dataclass), surfaced in `to_dict()`.
  - `service.get_user_by_issuer_sub(conn, issuer: str, sub: str) -> User | None`.
  - `users` table has `issuer TEXT NOT NULL` and unique `(issuer, authentik_uid)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_engine/test_users/test_issuer_model.py
from engine.users import service
from engine.users.models import User


def test_user_has_issuer_field():
    u = User(
        id="1", authentik_uid="sub-1", username="a", email=None,
        full_name=None, groups=None, issuer="https://id.example/app",
        created_at="t", last_seen_at="t", disabled_at=None,
    )
    assert u.issuer == "https://id.example/app"
    assert u.to_dict()["issuer"] == "https://id.example/app"


def test_get_user_by_issuer_sub_roundtrip(conn):
    created = service.upsert_from_headers(
        conn, {"X-Authentik-Uid": "sub-1", "X-Authentik-Username": "a"}
    )
    # upsert_from_headers stamps the cluster issuer (see Task 5 note); look it up
    found = service.get_user_by_issuer_sub(conn, created.issuer, "sub-1")
    assert found is not None
    assert found.id == created.id
    assert service.get_user_by_issuer_sub(conn, "other-iss", "sub-1") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `nix develop --command python -m pytest tests/test_engine/test_users/test_issuer_model.py -v`
Expected: FAIL — `TypeError: User.__init__() missing ... 'issuer'` / `get_user_by_issuer_sub` missing.

- [ ] **Step 3a: Migration (Postgres)**

```sql
-- db/migrations/012_user_issuer.sql
-- Distinguish identity populations sharing the users table: cluster-admin
-- Authentik (staff) vs the dedicated end-user Authentik. `issuer` is the OIDC
-- issuer URL; uniqueness moves from authentik_uid alone to (issuer, sub) so the
-- same subject id from two IdPs can't collide.
BEGIN;

ALTER TABLE users ADD COLUMN IF NOT EXISTS issuer TEXT;

-- Backfill existing rows: they all came from the cluster-admin Authentik.
UPDATE users
   SET issuer = COALESCE(NULLIF(current_setting('u4u.cluster_issuer', true), ''),
                         'cluster-authentik')
 WHERE issuer IS NULL;

ALTER TABLE users ALTER COLUMN issuer SET NOT NULL;

-- Replace the single-column uniqueness with the composite.
DROP INDEX IF EXISTS idx_users_authentik_uid;
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_issuer_uid ON users(issuer, authentik_uid);

COMMIT;
```

> Backfill value: the migration reads a PG session setting if present, else the literal `'cluster-authentik'`. Ops can set the real issuer before running via `SET u4u.cluster_issuer = '<url>'` in the same session, or accept the placeholder and reconcile later. Keep this consistent with `U4U_CLUSTER_AUTHENTIK_ISSUER` (Task 6).

- [ ] **Step 3b: SQLite mirror** — edit `engine/users/schema.sql` to match:

```sql
CREATE TABLE IF NOT EXISTS users (
    id              TEXT        PRIMARY KEY,
    authentik_uid   TEXT        NOT NULL,
    username        TEXT        NOT NULL,
    email           TEXT,
    full_name       TEXT,
    groups          TEXT,
    issuer          TEXT        NOT NULL DEFAULT 'cluster-authentik',
    created_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    last_seen_at    TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    disabled_at     TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_issuer_uid ON users(issuer, authentik_uid);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
```

- [ ] **Step 3c: `User` dataclass** — add `issuer: str` after `groups` in `engine/users/models.py`, and add `"issuer": self.issuer,` to `to_dict()`. (Field order must match the dataclass constructor used by tests; put `issuer` before `created_at`.)

- [ ] **Step 3d: `get_user_by_issuer_sub`** — add to `engine/users/service.py`:

```python
def get_user_by_issuer_sub(conn, issuer: str, sub: str) -> User | None:
    ph = _ph(conn)
    row = conn.execute(
        f"SELECT * FROM users WHERE issuer = {ph} AND authentik_uid = {ph}",
        (issuer, sub),
    ).fetchone()
    return User(**_row(row)) if row else None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `nix develop --command python -m pytest tests/test_engine/test_users/ -v`
Expected: PASS. (This depends on Task 5's issuer-stamping in `upsert_from_headers`; if running Task 4 alone, the second test may need Task 5 — implement Tasks 4 and 5 back-to-back and commit together if so.)

- [ ] **Step 5: Add a Postgres-smoke assertion** in `tests/test_postgres_smoke.py` `test_migrations_recorded`: assert `"012_user_issuer.sql" in applied`, and add a new test that `users` has an `issuer` column that is `NOT NULL`.

- [ ] **Step 6: Commit**

```bash
git add db/migrations/012_user_issuer.sql engine/users/schema.sql engine/users/models.py engine/users/service.py tests/test_engine/test_users/test_issuer_model.py tests/test_postgres_smoke.py
git commit -m "feat(auth): add users.issuer column + (issuer,sub) uniqueness (migration 012)"
```

---

### Task 5: `upsert_from_token` + issuer-aware `upsert_from_headers`

**Files:**
- Modify: `engine/users/service.py`
- Test: `tests/test_engine/test_users/test_upsert_from_token.py`

**Interfaces:**
- Consumes: `User` with `issuer` (Task 4).
- Produces:
  - `service.upsert_from_token(conn, *, issuer: str, claims: Mapping) -> User` — upsert keyed on `(issuer, sub)`; maps `sub`→authentik_uid, `email`, `name`→full_name, `preferred_username`→username; `groups` left empty for end-users.
  - `upsert_from_headers` now stamps `issuer = cluster_issuer_value` (from `oidc.cluster_issuer()` or the `'cluster-authentik'` fallback) and conflicts on `(issuer, authentik_uid)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_engine/test_users/test_upsert_from_token.py
from engine.users import service

_ISS = "https://id.example/app"


def test_upsert_from_token_creates_then_updates(conn):
    u1 = service.upsert_from_token(
        conn, issuer=_ISS,
        claims={"sub": "abc", "email": "a@b.co", "name": "A B",
                "preferred_username": "ab"},
    )
    assert u1.issuer == _ISS
    assert u1.authentik_uid == "abc"
    assert u1.email == "a@b.co"
    assert u1.groups in (None, "")  # end-users get no staff groups

    u2 = service.upsert_from_token(
        conn, issuer=_ISS,
        claims={"sub": "abc", "email": "new@b.co", "name": "A B",
                "preferred_username": "ab"},
    )
    assert u2.id == u1.id           # same row (composite key)
    assert u2.email == "new@b.co"   # profile re-mirrored from token


def test_same_sub_different_issuer_is_distinct(conn):
    a = service.upsert_from_token(conn, issuer=_ISS, claims={"sub": "x"})
    b = service.upsert_from_token(conn, issuer="https://other/idp", claims={"sub": "x"})
    assert a.id != b.id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `nix develop --command python -m pytest tests/test_engine/test_users/test_upsert_from_token.py -v`
Expected: FAIL — `AttributeError: module 'engine.users.service' has no attribute 'upsert_from_token'`.

- [ ] **Step 3: Implement** — add to `engine/users/service.py` (mirror the two-branch PG/SQLite upsert in `upsert_from_headers`, but conflict on `(issuer, authentik_uid)` and source fields from `claims`):

```python
from .oidc import cluster_issuer

_CLUSTER_ISSUER_FALLBACK = "cluster-authentik"


def _upsert_user(conn, *, issuer, sub, username, email, full_name, groups) -> User:
    ph = _ph(conn)
    is_pg = getattr(conn, "_is_pg", False)
    new_id = _new_id()
    cols = "(id, authentik_uid, username, email, full_name, groups, issuer)"
    vals = (new_id, sub, username, email, full_name, groups, issuer)
    conflict = "(issuer, authentik_uid)"
    if is_pg:
        row = conn.execute(
            f"""INSERT INTO users {cols}
                VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph})
                ON CONFLICT {conflict} DO UPDATE SET
                    username = EXCLUDED.username, email = EXCLUDED.email,
                    full_name = EXCLUDED.full_name, groups = EXCLUDED.groups,
                    last_seen_at = NOW()
                RETURNING *""",
            vals,
        ).fetchone()
        conn.commit()
        return User(**_row(row))
    conn.execute(
        f"""INSERT INTO users {cols}
            VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph})
            ON CONFLICT {conflict} DO UPDATE SET
                username = excluded.username, email = excluded.email,
                full_name = excluded.full_name, groups = excluded.groups,
                last_seen_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')""",
        vals,
    )
    conn.commit()
    return get_user_by_issuer_sub(conn, issuer, sub)


def upsert_from_token(conn, *, issuer: str, claims) -> User:
    sub = str(claims["sub"]).strip()
    username = (claims.get("preferred_username") or claims.get("email") or sub).strip()
    email = (claims.get("email") or "").strip() or None
    full_name = (claims.get("name") or "").strip() or None
    return _upsert_user(conn, issuer=issuer, sub=sub, username=username,
                        email=email, full_name=full_name, groups=None)
```

Then refactor `upsert_from_headers` to compute `issuer = cluster_issuer() or _CLUSTER_ISSUER_FALLBACK` and delegate to `_upsert_user(...)` with `groups` from the header (staff keep their groups).

- [ ] **Step 4: Run tests**

Run: `nix develop --command python -m pytest tests/test_engine/test_users/ -v`
Expected: PASS (including Task 4's roundtrip test now).

- [ ] **Step 5: Commit**

```bash
git add engine/users/service.py tests/test_engine/test_users/test_upsert_from_token.py
git commit -m "feat(auth): upsert_from_token + issuer-aware upsert_from_headers"
```

---

### Task 6: Auth dependencies — Bearer validation + dev bypass

**Files:**
- Modify: `engine/users/deps.py`
- Modify: `engine/users/api.py` (`/users/me` uses the new dependency)
- Test: `tests/test_engine/test_users/test_deps_auth.py`

**Interfaces:**
- Consumes: `oidc.oidc_settings` (T2), `token_validator.validate_token` (T3), `service.upsert_from_token` (T5).
- Produces:
  - `current_user(request) -> User | None` — soft. In dev-bypass mode returns the fixed dev user; in OIDC mode returns the token's user or `None` when no/invalid token.
  - `required_user(request) -> User` — hard. 401 when unauthenticated in OIDC mode; JWKS failure → 503; dev-bypass always returns the dev user.
  - `DEV_BYPASS_SUB = "dev-bypass"` constant (dev user's `authentik_uid`; issuer `"dev-bypass"`).

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `nix develop --command python -m pytest tests/test_engine/test_users/test_deps_auth.py -v`
Expected: FAIL — new symbols (`DEV_BYPASS_SUB`, token path) don't exist yet.

- [ ] **Step 3: Implement `engine/users/deps.py`**

```python
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
    settings = oidc.oidc_settings()
    with get_conn() as conn:
        if settings is None:
            # Dev / test: no IdP configured — inject a stable dev user.
            return service.upsert_from_token(
                conn, issuer=_DEV_ISSUER,
                claims={"sub": DEV_BYPASS_SUB, "preferred_username": "dev"},
            )
        token = _bearer(request)
        if token is None:
            return None
        claims = validate_token(token, settings)  # raises on bad token / JWKS
        return service.upsert_from_token(conn, issuer=settings.issuer, claims=claims)


def required_user(request: Request) -> User:
    try:
        user = current_user(request)
    except JwksUnavailable:
        raise HTTPException(status_code=503, detail="identity provider unavailable")
    except TokenError:
        raise HTTPException(status_code=401, detail="invalid access token")
    if user is None:
        raise HTTPException(status_code=401, detail="authentication required")
    return user
```

> Note: `current_user` (soft) must not 401, but it *may* raise `TokenError`/`JwksUnavailable` from `validate_token`. Wrap the `validate_token` call in `current_user` so a *malformed* token in soft contexts returns `None` (treat as anonymous) while `required_user` maps a *present-but-invalid* token to 401. Decide per the tests above: `required_user` catches and maps; `current_user` returns `None` on `TokenError` and re-raises `JwksUnavailable` (fail closed). Adjust the two functions so all five tests pass.

- [ ] **Step 4: Update `/users/me`** in `engine/users/api.py` to use `Depends(required_user)` and return `user.to_dict()` (drop the header-reading body). Keep `GET /users` as-is (admin view).

- [ ] **Step 5: Run tests**

Run: `nix develop --command python -m pytest tests/test_engine/test_users/ tests/test_current_user.py -v`
Expected: PASS. Update `tests/test_current_user.py` if it asserted the old header-only behavior.

- [ ] **Step 6: Commit**

```bash
git add engine/users/deps.py engine/users/api.py tests/test_engine/test_users/test_deps_auth.py tests/test_current_user.py
git commit -m "feat(auth): Bearer token auth dependencies with dev bypass"
```

---

### Task 7: Ownership guard + jobs endpoints

**Files:**
- Create: `engine/users/ownership.py`
- Modify: `api.py` (jobs endpoints + `_public_job`)
- Test: `tests/test_engine/test_jobs_ownership.py`

**Interfaces:**
- Consumes: `required_user` (T6), `User`.
- Produces: `ownership.owns(resource_owner_id: str | None, user: User) -> bool` and `ownership.guard_owner(resource_owner_id, user) -> None` (raises `HTTPException(404)` when not owned). Rule: `True` iff `resource_owner_id is not None and resource_owner_id == user.id`. NULL owner → not owned → 404.

- [ ] **Step 1: Write the failing test** (drive via `TestClient`; dev-bypass means all requests are the same dev user, so a job created by that user is readable, and a job with a *different* stored owner is 404):

```python
# tests/test_engine/test_jobs_ownership.py
import api
from fastapi.testclient import TestClient


def _seed_job(owner):
    jid = "job-" + (owner or "none")
    with api._jobs_lock:
        api._jobs[jid] = {
            "status": "complete", "progress": {"step": "done", "pct": 100},
            "count": 0, "results": {"variants": []}, "partial_results": [],
            "error": None, "filename": "f.vcf", "file_size": 1,
            "created_at": "2026-01-01T00:00:00+00:00", "started_at": None,
            "finished_at": None, "created_by_user_id": owner,
        }
    return jid


def test_owner_can_read_own_job(monkeypatch):
    with TestClient(api.app) as c:
        # discover the dev user's id, then own a job as them
        me = c.get("/users/me").json()
        jid = _seed_job(me["id"])
        assert c.get(f"/jobs/{jid}").status_code == 200


def test_other_users_job_is_404(monkeypatch):
    with TestClient(api.app) as c:
        jid = _seed_job("someone-else")
        assert c.get(f"/jobs/{jid}").status_code == 404


def test_null_owner_job_is_404(monkeypatch):
    with TestClient(api.app) as c:
        jid = _seed_job(None)
        assert c.get(f"/jobs/{jid}").status_code == 404


def test_public_job_does_not_leak_owner(monkeypatch):
    with TestClient(api.app) as c:
        me = c.get("/users/me").json()
        jid = _seed_job(me["id"])
        body = c.get(f"/jobs/{jid}").json()
        assert "created_by_user_id" not in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `nix develop --command python -m pytest tests/test_engine/test_jobs_ownership.py -v`
Expected: FAIL — endpoints currently return 200 for any job and leak the owner.

- [ ] **Step 3a: Implement `engine/users/ownership.py`**

```python
from __future__ import annotations

from fastapi import HTTPException

from .models import User


def owns(resource_owner_id: str | None, user: User) -> bool:
    return resource_owner_id is not None and resource_owner_id == user.id


def guard_owner(resource_owner_id: str | None, user: User) -> None:
    if not owns(resource_owner_id, user):
        # 404 (not 403): do not reveal that the id exists.
        raise HTTPException(status_code=404, detail="not found")
```

- [ ] **Step 3b: Strip the owner from client payloads** — in `api.py` `_public_job` (line ~206), after `response = dict(job)`, add `response.pop("created_by_user_id", None)`.

- [ ] **Step 3c: Guard each jobs endpoint.** Add `user: User = Depends(required_user)` to the signature and call the guard after fetching the job. Import at top of `api.py`: `from engine.users.deps import required_user` and `from engine.users.ownership import guard_owner`. Apply to:

  - `get_job` (api.py:674) — after `job = _jobs.get(job_id)` existence check, `guard_owner(job.get("created_by_user_id"), user)`.
  - `get_dossier` (api.py:732), `get_pgx` (api.py:759), `get_drug` (api.py:774), `acmg_signoff` (api.py:807) — same: fetch job, existence 404, then `guard_owner(...)`.
  - `list_jobs` (api.py:717) — add `user: User = Depends(required_user)`, and filter: only include jobs where `owns(job.get("created_by_user_id"), user)`. Import `owns` too.
  - `analyze` (api.py:577) — change `Depends(current_user)` to `Depends(required_user)` so every new job has a real owner (dev user in dev). Keep the `user.id` stamp at line 643.

  Worked example (`get_job`):

```python
@app.get("/jobs/{job_id}")
def get_job(job_id: str, include_results: bool = True,
            user: User = Depends(required_user)):
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    guard_owner(job.get("created_by_user_id"), user)
    return _public_job(job_id, job, include_results=include_results)
```

- [ ] **Step 4: Run tests + full suite**

Run: `nix develop --command python -m pytest tests/test_engine/test_jobs_ownership.py tests/ -q`
Expected: PASS. Fix any existing job tests that assumed open access (they must now go through `/users/me` to own their seeded jobs, or seed with the dev user's id).

- [ ] **Step 5: Commit**

```bash
git add engine/users/ownership.py api.py tests/test_engine/test_jobs_ownership.py
git commit -m "feat(auth): enforce job ownership + stop leaking owner id (closes IDOR on jobs)"
```

---

### Task 8: Ownership guard on tracking endpoints

**Files:**
- Modify: `engine/tracking/api.py`
- Modify: `engine/tracking/service.py` (owner-aware reads where needed)
- Test: `tests/test_engine/test_tracking/test_ownership.py`

**Interfaces:**
- Consumes: `required_user` (T6), `guard_owner`/`owns` (T7), `_user_id` helper (existing).
- Produces: every per-patient tracking endpoint requires the caller to own the patient; `list_patients` returns only the caller's patients.

**Pattern:** the owning resource is the **patient** (`patients.created_by_user_id`). Treatments/measurements/genetics/predictions/priors all hang off a `patient_id`, so guarding is: load the patient, `guard_owner(patient.created_by_user_id, user)`, then proceed. `service.get_patient` returns a `Patient`; confirm it carries `created_by_user_id` (it selects `*`), else add it to the `Patient` dataclass first.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_engine/test_tracking/test_ownership.py
import api
from fastapi.testclient import TestClient


def test_list_patients_scoped_to_owner():
    with TestClient(api.app) as c:
        r = c.post("/tracking/patients", json={"label": "MINE"})
        pid = r.json()["id"]
        listed = c.get("/tracking/patients").json()
        assert any(p["id"] == pid for p in listed)


def test_foreign_patient_is_404():
    # Seed a patient owned by someone else directly via the service.
    from engine.tracking import db as tdb, service
    with tdb.get_conn() as conn:
        other = service.create_patient(conn, label="THEIRS",
                                        created_by_user_id="someone-else")
    with TestClient(api.app) as c:
        assert c.get(f"/tracking/patients/{other.id}").status_code == 404
        assert c.get(f"/tracking/patients/{other.id}/predictions",
                     params={"peptide": "BPC-157", "biomarker": "CRP"}).status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `nix develop --command python -m pytest tests/test_engine/test_tracking/test_ownership.py -v`
Expected: FAIL — reads currently return 200 for any patient.

- [ ] **Step 3: Implement.** Add `from engine.users.deps import required_user`, `from engine.users.ownership import guard_owner, owns`, and `from engine.users.models import User` to `engine/tracking/api.py`. Add a small helper:

```python
def _require_owned_patient(conn, patient_id: str, user: User):
    patient = service.get_patient(conn, patient_id)
    if patient is None:
        raise HTTPException(404, "patient not found")
    guard_owner(getattr(patient, "created_by_user_id", None), user)
    return patient
```

Apply per endpoint (add `user: User = Depends(required_user)` to each signature):

  - **Owner-scoped list** — `list_patients` (#2, line 104): filter `service.list_patients(conn)` to `owns(p.created_by_user_id, user)`.
  - **Guard-by-patient** — `get_patient` (#3), `delete_patient` (#4), `list_treatments` (#6), `list_measurements` (#10), `get_genetics` (#14), `generate_genetics` (#15), `get_predictions` (#17), `get_priors` (#18): call `_require_owned_patient(conn, patient_id, user)` before the existing logic.
  - **Create-under-patient** — `create_treatment` (#5), `create_measurement` (#7), `bulk_measurements` (#8), `upload_csv` (#9): these already take `current_user`; switch to `required_user` and guard the target patient before insert (measurement/treatment bodies carry `patient_id`).
  - **`create_patient` (#1)** — switch `current_user`→`required_user` so new patients always have a real owner.
  - **`create_patient_from_job` (#16)** — switch to `required_user`; additionally guard the *job*: after `get_completed_job_results(job_id)`, verify the job's `created_by_user_id` equals `user.id` (else 404) so a user can't seed a patient from someone else's job. (Add a `get_job_owner(job_id)` accessor in `api.py` alongside `get_completed_job_results`.)
  - **Stays public / unchanged:** `GET /tracking/peptides` (#11), `/tracking/peptides/{}/biomarkers` (#12), `/tracking/cohort` (#13, aggregate) — leave unauthenticated. `POST /tracking/seed` (#19): gate behind `required_user` **and** the dev-bypass — i.e. only allow when `oidc.oidc_settings() is None` (dev/demo); return 403 in configured/prod mode. Document this.

- [ ] **Step 4: Run tests + full suite**

Run: `nix develop --command python -m pytest tests/test_engine/test_tracking/ tests/ -q`
Expected: PASS. Update `tests/test_engine/test_tracking/test_api.py` where it created a patient then read it back — with the dev-bypass user this still works (same owner), but any test that seeded via the service with a *different* or NULL owner and then read via the API must be updated to use the dev user's id or go through the API.

- [ ] **Step 5: Commit**

```bash
git add engine/tracking/api.py engine/tracking/service.py tests/test_engine/test_tracking/test_ownership.py tests/test_engine/test_tracking/test_api.py
git commit -m "feat(auth): enforce patient ownership across tracking endpoints (closes IDOR)"
```

---

### Task 9: Frontend Bearer plumbing + docs

**Files:**
- Modify: `frontend/src/app/lib/authFetch.ts`
- Modify: `docs/server-management.md` (or CLAUDE.md env table) — document the new env vars
- Test: manual / existing frontend build

**Interfaces:**
- Consumes: an access token obtained by the SPA (full OIDC login UI is a **follow-on task, blocked on the real Authentik existing** — see spec's external dependencies).

- [ ] **Step 1:** In `frontend/src/app/lib/authFetch.ts`, attach `Authorization: Bearer <token>` from the in-memory token store when present; leave requests unauthenticated when absent (dev). (No token store yet → this is a no-op scaffold that later OIDC work fills in.)

- [ ] **Step 2:** Document the new backend env vars in the CLAUDE.md "Key Environment Variables" table: `U4U_OIDC_ISSUER`, `U4U_OIDC_AUDIENCE`, `U4U_OIDC_JWKS_URL`, `U4U_CLUSTER_AUTHENTIK_ISSUER` — noting that when the three `U4U_OIDC_*` are unset the API runs in dev-bypass (single dev user, no auth).

- [ ] **Step 3:** Run `cd frontend && npm run build` to confirm the type-checks pass.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/lib/authFetch.ts CLAUDE.md
git commit -m "feat(auth): frontend Bearer plumbing + document OIDC env vars"
```

> **Deferred (follow-on, blocked on Hampton provisioning the end-user Authentik):** the SPA OIDC login/callback/logout flow, the in-memory token store + silent refresh, and the `/login` + `/profile` pages. Build these once the issuer/JWKS/client exist; they can be integration-tested only against the real (or a locally stood-up) Authentik.

---

## Self-Review

**Spec coverage:**
- Dedicated Authentik OIDC (§Components 1) → Tasks 2, 3, 6 (config, validation, dependency) + Task 9 note (frontend login deferred, blocked on IdP). ✓
- Frontend Bearer (§2) → Task 9 (plumbing); full login flow explicitly deferred with rationale. ✓
- Backend token validation (§3) → Tasks 3, 6. ✓
- Data model / migration 012 (§4) → Task 4. ✓
- Access control / IDOR (§5) → Tasks 7 (jobs) + 8 (tracking); 404-on-mismatch, NULL-owner inaccessible. ✓
- Dev/test bypass (§6) → Task 6. ✓
- Testing (§7): RSA/JWKS validator tests (T3), ownership tests (T7, T8), migration in PG smoke (T4). ✓
- Error handling table (401/404/503) → T3 (503 fail-closed), T6 (401), T7/T8 (404). ✓

**Placeholder scan:** No "TBD/TODO/handle edge cases" — every code step shows code. The one intentional deferral (frontend login UI) is scoped with its blocking dependency, not left vague.

**Type consistency:** `User` gains `issuer: str` (T4) and is constructed with it everywhere; `upsert_from_token(conn, *, issuer, claims)` signature is consistent across T5/T6; `guard_owner(resource_owner_id, user)` / `owns(...)` names consistent across T7/T8; `required_user`/`current_user` consistent T6→T7/T8.

**Scope:** Single coherent unit (identity + access control). Billing/sharing/notifications and the SPA login UI are out (own specs / blocked follow-on).
