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
| `auth.py` | `Authorization: Bearer <token>` → app user, via SHA-256 token hash lookup. |
| `schemas.py` | Pydantic models accepting the app's camelCase JSON (`typeIdentifier`, …). |
| `api.py` | `POST /health-samples` (idempotent upsert), `GET /health-samples/summary`. |
| `db/migrations/008_healthkit_ingestion.sql` | The same tables as SQL, for production/manual apply. |
| `scripts/create_device_token.py` | Mint a per-device bearer token (shown once). |

### Endpoints

```
POST /health-samples            Authorization: Bearer <token>
  { "samples": [ { "uuid": "…", "typeIdentifier": "HKQuantityTypeIdentifierHeartRate",
                   "kind": "quantity", "startDate": "…", "endDate": "…",
                   "value": 62, "unit": "count/min", … } ] }
  → { "received": N }           # upsert by (user_id, uuid) — safe to retry

GET  /health-samples/summary    → { "user_id": "…", "sample_count": N }
```

Idempotency is the composite PK `(user_id, uuid)`: the client is at-least-once,
and re-delivered samples update in place.

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
production home, added by **iac PR #82**. hwcopeland supplied the `u4u` Bitwarden
item UUID in review, so the secret prerequisite is resolved; the UUID paste and a
rebase off a stale base remain, both in the infra owner's domain.

## Anonymization (planned follow-up, not a blocker)

The trial will need HealthKit data de-identified. **Decision: simple first,
anonymize later** — the initial store keys samples to an `app_users` row carrying
an email; a later pass adds the de-identification the observational protocol
requires (the `u4u-privacy` repo is a likely home). Tracked as follow-up, not a
gate on the first working path.
