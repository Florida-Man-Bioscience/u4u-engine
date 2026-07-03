# HealthKit data storage — design & auth

The peptodyssey iOS app syncs HealthKit samples to the engine over HTTPS; the
engine stores them de-identified in Postgres. This is the design/reference doc;
for how to run it see [`healthkit-ingestion-setup.md`](healthkit-ingestion-setup.md).

> **A phone never talks to Postgres directly.** The app POSTs batches to an
> ingestion endpoint that writes to Postgres — schema + endpoint + database, not
> an exposed `:5432`.

## Implementation (`engine/healthkit`)

Sync (psycopg2) module using the same `db.pool` connection as the rest of the
engine, with a SQLite fallback for dev/tests (so no live DB is needed to run the
suite). Active whenever the app hits the endpoint; with no `DATABASE_URL` it
writes to a local SQLite file.

| Piece | What |
|---|---|
| `api.py` | `POST /healthkit/samples` (idempotent), `GET /healthkit/samples`. |
| `service.py` | Ingest + read; `_ph()`/`_row()` pattern shared with `engine/tracking`. |
| `schemas.py` | Pydantic request bodies (`subjectId`, `samples[]`, optional `anchors`). |
| `db.py` | Postgres-or-SQLite `get_conn()` switch (same as tracking/users). |
| `db/migrations/008_healthkit.sql` | Postgres schema (auto-applied by `db/migrate.py`). |
| `engine/healthkit/schema.sql` | SQLite schema for dev/tests (kept in lockstep). |

### Endpoints

```
POST /healthkit/samples
  Authorization: (see Authentication — currently soft/optional)
  { "subjectId": "<app-generated opaque id>",
    "samples": [ { "uuid": "…", "class": "quantity",
                   "type": "HKQuantityTypeIdentifierHeartRate",
                   "value": 62, "unit": "count/min",
                   "start": "…", "end": "…", "source": {"name": "Apple Watch"} } ],
    "anchors": { "HKQuantityTypeIdentifierHeartRate": "<base64 HKQueryAnchor>" } }
  → { "received": N, "inserted": M }   # M = genuinely new rows

GET  /healthkit/samples?subject_id=…&type=…&since=…&limit=…
```

### Data model (`healthkit_*`)

Opaque, de-identified: `healthkit_subjects` (an app-assigned `subject_id` — no
name/DOB/Apple id), `healthkit_samples` (one wide row per sample, keyed by device
`HKSample.uuid`), `healthkit_workouts`, `healthkit_sync_anchors` (mirrors the
client's `HKAnchoredObjectQuery` anchors), `healthkit_ingestions` (per-batch
audit).

**Idempotency & a known limit:** samples are **insert-only** —
`ON CONFLICT (sample_uuid) DO NOTHING` — so re-syncs and anchored-query replays
are safe. Trade-off (acceptable under "simple first"): there is **no update path
and no `is_deleted`**, so if a sample is edited or deleted in HealthKit that
change does **not** propagate; the first-seen version is retained. Revisit if the
study needs mutable/soft-deleted samples.

## Authentication

Two models are in play. **What ships today is the soft forward-auth path; the
device-code flow is the target.** Get the config values (issuer, client_id) from
[Authentik provisioning](#authentik-configuration--provisioning) — they do not
exist yet.

### Current — Authentik forward-auth (soft)

The endpoint depends on `current_user`, which reads Authentik proxy headers
(`X-Authentik-Uid`, …). If present, the operator is recorded in the ingestion
audit; **it does not gate ingestion**.

> ⚠️ **Open write endpoint (known gap).** There is **no Authentik forward-auth
> proxy in front of `flmanbiosci.net/api/v1` today**, so those headers are never
> injected and the endpoint accepts **unauthenticated** writes. This is fine
> pre-prod — HealthKit ingestion is not live (no `DATABASE_URL` until iac PR #82
> merges) — but **must be hardened before public exposure**. The code logs a
> one-time warning when an unauthenticated request lands (so it is not silent).
> To close it, pick one: (a) deploy an Authentik forward-auth proxy in front of
> `/api/v1/healthkit/*`; (b) switch to the device-code flow below; or (c) an
> interim per-device bearer token.

### App-generated opaque `subjectId`

The app generates **once, on first launch**, a random opaque id (UUID v4),
persists it in the Keychain, and sends it as `subjectId` on every upload:

- **PII-free** — a random UUID, not an email/name/serial. It is the pseudonymous
  key samples are stored under, so rows carry no direct identifier (this is the
  de-identification the trial needs — see [Anonymization](#anonymization)).
- **Stable** — same value for the life of the install, so the
  `ON CONFLICT (sample_uuid)` idempotency and per-subject reads stay consistent.
  Regenerating it orphans prior data.
- When auth is hardened, bind `subjectId ↔ authenticated identity` server-side on
  first sight so one user can't write to another's `subjectId`.

### Target — Authentik OAuth 2.0 Device Authorization Grant

Better fit than forward-auth for a native app calling `/api/v1` directly (no
proxy needs to sit in the request path). The app obtains a token via the device
code flow and sends `Authorization: Bearer <access_token>`; the backend validates
it (JWKS) and maps the `sub` claim to the operator/subject binding.

1. `POST` the device authorization endpoint with `client_id` + `scope` → get
   `device_code`, `user_code`, `verification_uri`, `interval`.
2. Show `user_code`/`verification_uri`; user approves in a browser.
3. Poll the token endpoint (`grant_type=urn:ietf:params:oauth:grant-type:device_code`)
   until it returns `access_token` (+ `refresh_token`).
4. Store tokens in the Keychain; refresh as needed; send the bearer on every call.

Backend (to implement): validate the JWT via the issuer's JWKS, check `iss`/`aud`/`exp`,
take `sub` as the stable subject.

### Authentik configuration & provisioning

Authentik is live at **`https://auth.hwcopeland.net`** with standard per-provider
OIDC endpoints. The **app-specific values are net-new — no OAuth2 provider exists
for this app yet** (proposed slug `peptodyssey`):

| Value | Setting |
|---|---|
| Authorization server | `https://auth.hwcopeland.net` *(exists)* |
| Issuer (`iss`) | `https://auth.hwcopeland.net/application/o/peptodyssey/` — **TBD** |
| OIDC discovery | `…/application/o/peptodyssey/.well-known/openid-configuration` |
| `client_id` | **TBD** — assigned on provider creation (propose `peptodyssey`, **public** client) |
| Device authorization endpoint | `https://auth.hwcopeland.net/application/o/device/` *(confirm via discovery)* |
| Token endpoint | `https://auth.hwcopeland.net/application/o/token/` |
| Scopes | `openid profile email offline_access` |

Provisioning is an Authentik/iac task (`rke2/authentik/`, Hampton's domain):
create a public OAuth2 Provider with the **device-code flow enabled** and an
Application (slug `peptodyssey`), then fill the TBD values above.

## Production path

The in-cluster Postgres (`u4u-postgres`, iac **PR #82**) is the production home.
That PR is ready (clean 3-file diff, real Bitwarden UUID in place,
`mergeable=CLEAN`); the merge is the repo owner's (hwcopeland's) call since it
deploys to the live cluster. On merge, Flux wires `DATABASE_URL` into the backend
and this datastore activates — **at which point the open-endpoint gap above
becomes live**, so harden auth before/with that.

## Anonymization

Already de-identified by design: samples are keyed to the opaque `subjectId`, so
the health rows carry no direct identifier — this is the posture the observational
trial needs, achieved up front rather than as a later scrub.
