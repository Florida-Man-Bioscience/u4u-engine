# End-user authentication + access control (Phase 1 of the member portal)

**Status:** Design approved 2026-07-09. Ready for implementation planning.
**Scope:** First sub-project of the "full member portal." Covers end-user
identity (login/session/profile) and resource-level access control (closing
the known IDOR gap). Billing, clinician data-sharing, and notifications are
**out of scope** — each is a separate follow-on spec.

## Background

Today the API trusts `X-Authentik-*` request headers forwarded by a proxy
(`engine/users/deps.py`). In production that proxy is not in front of the API,
so the headers are spoofable and the API is effectively unauthenticated; on top
of that, resource endpoints do not check ownership (IDOR). The existing `users`
table is keyed to the **cluster-admin Authentik** subject (`authentik_uid`) and
is meant for staff/operators.

Hampton has asked for **website end-user** accounts (patients/visitors) that are
*semi-isolated* from the cluster-admin Authentik. This spec adds that identity
population and makes every user's data accessible only to that user.

## Decisions (locked)

| Decision | Choice |
|---|---|
| Identity provider | **Dedicated Authentik via OIDC** (semi-isolated realm/instance for end-users) |
| First-spec scope | **Identity + access control together** (close IDOR in the same unit) |
| Auth placement | **API validates OIDC tokens directly** (stateless Bearer validation) |
| Ownership model | **Reuse `users` table with an `issuer` column** (no separate table) |
| Access-control response | **404 on ownership mismatch** (no existence leak); **401** when unauthenticated |

## Components

### 1. Dedicated Authentik (infrastructure — Hampton / `iac` repo)

A semi-isolated Authentik realm/instance for website end-users, deployed in the
`theswamp` namespace and reachable via in-cluster DNS. It exposes:

- an OIDC **issuer** URL + discovery document,
- a **JWKS** endpoint (signing keys),
- a **public client** for the SPA using Authorization Code + PKCE.

The app consumes three config values — issuer URL, expected audience/client id,
JWKS URL — provisioned as a **Bitwarden secret referenced by UUID** through the
External Secrets Operator (matching the existing secret flow). No PVC is
required, so the >100 GB PVC cluster policy does not apply.

**This component is an external dependency.** The application code in this spec
is built and tested against a *fake* issuer + locally generated JWKS, so it does
not block on the real Authentik existing. It cannot go **live** until Hampton
provisions the realm and secret.

### 2. Frontend (Next.js)

- Authorization Code + PKCE login against the end-user Authentik.
- Access token held **in memory** (not `localStorage`) to limit XSS token theft;
  silent refresh via Authentik's refresh flow.
- `Authorization: Bearer <access_token>` attached to API calls in
  `frontend/src/app/lib/authFetch.ts`.
- Routes: `/login`, `/logout`, the OIDC callback route, and a `/profile` page
  backed by `GET /users/me`.
- Because auth uses a Bearer header (no ambient cookie), **CSRF is not in scope**.

### 3. Backend token validation (FastAPI — the enforcement point)

A dependency (evolving `engine/users/deps.py`) that, per request:

1. Extracts the `Authorization: Bearer` token (401 if absent in prod).
2. Validates it against the end-user Authentik JWKS (keys fetched and **cached**,
   refreshed on unknown `kid`): signature, `iss` == end-user issuer, `aud` ==
   configured audience, `exp`/`nbf`.
3. Maps the verified (`iss`, `sub`) to a `users` row via a new
   `service.upsert_from_token(...)` — replacing header-based
   `upsert_from_headers` for end users. Claims (email, name) come from the
   **verified token**, never from client-settable headers.

The spoofable `X-Authentik-*` header path is removed for end-user auth. (Any
staff/header path that remains is gated to the cluster-Authentik issuer and is
Hampton's separate proxy track — not extended here.)

### 4. Data model — migration `012_user_issuer.sql`

- Add `issuer TEXT` to `users`.
- **Backfill** existing rows with the cluster-Authentik issuer constant.
- Make `issuer` `NOT NULL` after backfill.
- Replace the uniqueness constraint on `authentik_uid` with a composite unique
  `(issuer, authentik_uid)`; `authentik_uid` now holds the OIDC `sub` for
  whichever issuer.
- Mirror the change into `engine/users/schema.sql` (the SQLite dev/test schema)
  so the dual-schema stays in sync — see PR #80's smoke-test job, which will
  exercise this migration on Postgres.

**Population isolation:** end-user rows carry empty `groups`. Staff privileges
are only ever granted when `issuer` == the cluster-Authentik issuer, so a
website user can never be mistaken for staff despite sharing the table.

### 5. Access control — closes IDOR

A single reusable ownership guard used by every data endpoint:

- Require an authenticated user (else 401).
- Load the resource; if `resource.created_by_user_id != user.id`, return **404**
  (not 403 — avoids leaking that the id exists).
- Apply to: `GET`/`DELETE /jobs/{id}` and job results; tracking
  patients, treatments, measurements, genetics, predictions, priors, and
  `patients/from-job`.

**Legacy rows** with `created_by_user_id IS NULL` are inaccessible to end users
(treated as not-found). An admin backfill/adoption flow is deferred to a later
spec.

**Ownership on create:** create endpoints stamp `created_by_user_id` from the
authenticated user (the plumbing already exists via `_user_id(user)` and the
`005_ownership_fks` columns).

### 6. Dev / test mode

When **no end-user OIDC issuer is configured** (local dev, the test suite), a
bypass injects a fixed dev user so local ergonomics and the existing suite keep
working (mirrors today's soft-auth behavior). When an issuer **is** configured
(production), authentication is hard-required — a missing/invalid token is 401.
A test helper stamps a chosen user identity so ownership tests can act as
different users.

## Data flow (happy path)

```
Browser ──PKCE login──▶ End-user Authentik ──token──▶ Browser
Browser ──Bearer token──▶ FastAPI dep: validate vs JWKS ──▶ upsert users row
       ──▶ endpoint: ownership guard (created_by_user_id == user.id) ──▶ 200
```

## Error handling

| Situation | Response |
|---|---|
| No/blank Authorization header (prod) | 401 |
| Malformed / expired / bad-signature token | 401 |
| Valid token, wrong `iss` or `aud` | 401 |
| Valid user, resource owned by someone else | 404 |
| Valid user, resource does not exist | 404 |
| JWKS endpoint unreachable | 503 (fail closed; do not accept unverified tokens) |

## Testing

- **Token validation** (unit): local RSA keypair + fake JWKS — accept a valid
  token; reject expired, wrong-`iss`, wrong-`aud`, bad-signature, and
  unknown-`kid`. JWKS fail-closed path returns 503.
- **Ownership** (integration): owner gets 200; a different authenticated user
  gets 404; anonymous gets 401; NULL-owner legacy row is 404 for end users.
- **Migration 012**: exercised in the Postgres smoke job (backfill populates
  `issuer`; composite uniqueness holds; a duplicate `(issuer, sub)` upsert is a
  no-op update).
- SQLite suite and ruff stay green.

## Out of scope (follow-on specs)

- Billing / subscription + entitlements.
- Clinician data-sharing (grant/revoke access to another user's data).
- Notifications (email / in-app).
- Admin adoption/backfill of legacy NULL-owner rows.
- Staff/operator forward-auth proxy (Hampton's cluster-Authentik track).

## External dependencies / open items

- **Hampton:** provision the dedicated end-user Authentik realm/instance +
  Bitwarden secret (issuer, audience, JWKS URL) referenced by UUID.
- Confirm the exact cluster-Authentik issuer string used to backfill existing
  `users` rows in migration 012.
