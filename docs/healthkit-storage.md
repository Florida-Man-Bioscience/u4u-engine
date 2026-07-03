# HealthKit data storage — setup & design

The peptodyssey iOS app syncs HealthKit samples to the engine over HTTPS; the
engine stores them in Postgres. This doc covers the implementation
(`engine/health`), local dev, and the production path.

> **A phone never talks to Postgres directly.** The app POSTs batches to an
> authenticated ingestion endpoint that writes to Postgres — so "a Postgres
> server for HealthKit data" means **schema + endpoint + database**, not an
> exposed `:5432`.

## Implementation (`engine/health`)

Async SQLAlchemy 2.0 module, mounted by `api.py`. Active only when
`DATABASE_URL` is set; otherwise the endpoints return 503 and the rest of the
engine is unaffected.

| Piece | What |
|---|---|
| `models.py` | `app_users`, `device_tokens`, `health_samples` (SQLAlchemy ORM). |
| `db.py` | Lazy async engine + session factory. Derives an `asyncpg` URL from `DATABASE_URL` (see below). |
| `auth.py` | `Authorization: Bearer <token>` → app user. **Currently** a SHA-256 device-token lookup; the **target** is an Authentik-issued token (see [Authentication](#authentication-authentik--oauth-20-device-authorization-grant)). |
| `schemas.py` | Pydantic models accepting the app's camelCase JSON (`typeIdentifier`, …). |
| `api.py` | `POST /health-samples` (idempotent upsert), `GET /health-samples/summary`. |
| `db/migrations/008_healthkit_ingestion.sql` | The same tables as SQL, for production/manual apply. |
| `scripts/create_device_token.py` | Mint a per-device bearer token (shown once). |

### Endpoints

```
POST /health-samples
  Authorization: Bearer <token>       # target: Authentik access token (see Authentication)
  { "subjectId": "<app-generated opaque id>",   # target: pseudonymous subject key
    "samples": [ { "uuid": "…", "typeIdentifier": "HKQuantityTypeIdentifierHeartRate",
                   "kind": "quantity", "startDate": "…", "endDate": "…",
                   "value": 62, "unit": "count/min", … } ] }
  → { "received": N }           # upsert by (subject, uuid) — safe to retry

GET  /health-samples/summary    → { "user_id": "…", "sample_count": N }
```

Idempotency is the composite PK `(subject, uuid)`: the client is at-least-once,
and re-delivered samples update in place. See [Authentication](#authentication-authentik--oauth-20-device-authorization-grant)
for how `Authorization` and `subjectId` are defined.

### `app_users` vs the platform `users`

The app's end-users live in **`app_users`** (email + device tokens) — a separate
table and population from the platform's **`users`** (Authentik-backed operators,
`db/migrations/004_users.sql`). They are not merged. *(Integration note: the
Xcode branch originally named this table `users`, which collided with the
operator table; renamed here to `app_users`. Flagged for the architecture owner
in the PR.)*

### One `DATABASE_URL`, two drivers

The engine's existing stack (annotation cache, rsID cache, tracking, job store,
migrations) uses **sync psycopg2** with `postgresql://…?sslmode=disable`. This
module uses **async asyncpg**, which needs `postgresql+asyncpg://…` and rejects
`sslmode`. Rather than a second env var, `engine/health/db.py` **derives** the
async URL from the canonical sync `DATABASE_URL` (swaps the driver, drops
libpq-only params). One `DATABASE_URL` → one Postgres → both stacks.

## Authentication (Authentik — OAuth 2.0 Device Authorization Grant)

This section is the **auth contract for the peptodyssey iOS app** (so the Xcode
side can implement it). It has two parts: the request carries (1) an **Authentik
access token** proving the request comes from an authenticated user, and (2) an
**app-generated opaque `subjectId`** — the pseudonymous key the samples are
stored under (no PII, supports the "anonymize later" posture below).

> **Status.** The current code (`engine/health/auth.py`) uses a hand-minted
> `pep_` device token, not Authentik. The below is the **target**. Two things do
> not exist yet and must be created before it works end to end:
> 1. an Authentik OAuth2 provider/application for this app (see *Provisioning*);
> 2. the backend swap from device-token lookup to Authentik JWT validation +
>    `subjectId` binding. The iOS side can be built against this contract now;
>    until (1)/(2) land, keep using device tokens.

### Authentik configuration

Authentik is live at **`https://auth.hwcopeland.net`** with standard per-provider
OIDC endpoints. The app-specific values are **to be provisioned** — a new OAuth2
provider/application does not exist yet (proposed slug `peptodyssey`):

| Value | Setting |
|---|---|
| Authorization server | `https://auth.hwcopeland.net` *(exists)* |
| Issuer (`iss`) | `https://auth.hwcopeland.net/application/o/peptodyssey/` — **TBD** (per-provider issuer; depends on the app slug) |
| OIDC discovery | `https://auth.hwcopeland.net/application/o/peptodyssey/.well-known/openid-configuration` — read the exact endpoints/JWKS from here once the provider exists |
| `client_id` | **TBD** — assigned when the provider is created (propose `peptodyssey`) |
| Client type | **public** (native app, no client secret) — mirrors the existing `kubernetes` provider |
| Device authorization endpoint | `https://auth.hwcopeland.net/application/o/device/` *(confirm via discovery)* |
| Token endpoint | `https://auth.hwcopeland.net/application/o/token/` |
| JWKS URI | from discovery, e.g. `https://auth.hwcopeland.net/application/o/peptodyssey/jwks/` |
| Scopes | `openid profile email offline_access` (`offline_access` → refresh token) |
| Grant type | `urn:ietf:params:oauth:grant-type:device_code` (RFC 8628) |

### Device code flow (RFC 8628) — app side

Chosen because it needs no custom redirect URI / embedded web view: the user
approves in a normal browser and the app polls for the token.

1. **Request a device code** — `POST` the device authorization endpoint,
   form-encoded, with `client_id` and `scope`:
   ```
   POST https://auth.hwcopeland.net/application/o/device/
   Content-Type: application/x-www-form-urlencoded
   client_id=peptodyssey&scope=openid%20profile%20email%20offline_access
   ```
   Response: `device_code`, `user_code`, `verification_uri`,
   `verification_uri_complete`, `expires_in`, `interval`.
2. **Prompt the user** — show `user_code` and `verification_uri` (or open
   `verification_uri_complete`, which pre-fills the code). The user signs into
   Authentik in the browser and approves.
3. **Poll the token endpoint** every `interval` seconds until it stops returning
   `authorization_pending` / `slow_down`:
   ```
   POST https://auth.hwcopeland.net/application/o/token/
   Content-Type: application/x-www-form-urlencoded
   grant_type=urn:ietf:params:oauth:grant-type:device_code
   &device_code=<device_code>&client_id=peptodyssey
   ```
   Success returns `access_token` (JWT), `id_token`, `refresh_token`, `expires_in`.
4. **Store tokens in the Keychain.** Refresh with the `refresh_token`
   (`grant_type=refresh_token`) when the access token nears expiry; only re-run
   the device flow if the refresh token is gone/expired.
5. **Call the API** with `Authorization: Bearer <access_token>` on every
   `POST /health-samples`.

### Backend validation (target — to implement)

Replace the device-token lookup in `engine/health/auth.py` with JWT validation:
fetch the JWKS from the discovery document, verify the token's signature, `iss`
(== issuer above), `aud` (== `client_id`), and `exp`; the stable Authentik
subject is the `sub` claim.

### App-generated opaque `subjectId`

The app generates **once, on first launch**, a random opaque identifier
(UUID v4), persists it in the Keychain, and sends it as `subjectId` on every
upload. Properties:

- **Opaque & PII-free** — a random UUID, not an email, name, or device serial.
  It is the pseudonymous key the samples are stored under, so the health rows
  carry no direct identifier (supports [Anonymization](#anonymization-planned-follow-up-not-a-blocker)).
- **Stable** — the same value for the life of the install, so re-syncs and the
  `(subject, uuid)` upsert stay consistent. Regenerating it orphans prior data.
- **Bound to the authenticated user, not trusted blindly** — on the first
  authenticated request the backend records the mapping `Authentik sub ↔
  subjectId` and thereafter only accepts writes to that `subjectId` from the
  bound `sub`. This stops one user from claiming another's `subjectId`.

In the request body it is a top-level field alongside `samples`
(`schemas.py` → add `subject_id` / camelCase `subjectId` to `UploadBody`).

### Provisioning checklist (Authentik-side, net-new)

Authentik lives in the iac repo (`rke2/authentik/`, Hampton's domain), so this is
an infra task, not a code change here:

1. Create an **OAuth2 Provider** for the app: public client, issuer mode
   per-provider, scopes `openid profile email offline_access`, and **enable the
   Device code flow** (set the provider's device-code flow).
2. Create an **Application** (slug `peptodyssey`) bound to that provider; restrict
   access to the existing `Florida Man Bioscience` group if desired.
3. Read the real `client_id` and issuer from the created provider and fill in the
   TBD values above. Add the provider as a blueprint under `rke2/authentik/`
   (mirroring e.g. the `kubernetes` public client) so it's GitOps-managed.

## Local dev

`docker-compose.yml` runs a `postgres:16-alpine` service and defaults
`DATABASE_URL` to it (sync form). It mirrors the production StatefulSet (db/user
`u4u`) in the iac repo (`rke2/tooling/flux/theswamp/postgres.yaml`).

```bash
cp .env.example .env          # fill NCBI_API_KEY (DATABASE_URL defaults to the pg service)
docker compose up --build
# mint a token for the app:
docker compose exec api python scripts/create_device_token.py you@example.com --device "iPhone"
```

The engine auto-runs `db/migrate.py` on startup (applies migration 008); the
health module also `create_all()`s the same tables on boot as a fallback. With
no `DATABASE_URL`, the engine falls back to SQLite and health ingestion is off.

## Production path

The in-cluster Postgres (`u4u-postgres`, StatefulSet in the iac repo) is the
production home, added by **iac PR #82**. That PR is now ready — rebased to a
clean 3-file diff with the real Bitwarden UUID in place, `mergeable=CLEAN`. The
only remaining step is the merge, which is the repo owner's (hwcopeland's) call
since it deploys to the live cluster. On merge, Flux applies the StatefulSet and
wires `DATABASE_URL` into the backend, activating this datastore.

## Anonymization (planned follow-up, not a blocker)

The trial will need HealthKit data de-identified. **Decision: simple first,
anonymize later** — the initial store keys samples to an `app_users` row carrying
an email; a later pass adds the de-identification the observational protocol
requires (the `u4u-privacy` repo is a likely home). Tracked as follow-up, not a
gate on the first working path.
