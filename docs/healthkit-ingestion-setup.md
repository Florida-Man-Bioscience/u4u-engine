# HealthKit ingestion — setup

How to run and configure the `POST /healthkit/samples` endpoint that receives
Apple HealthKit data from the **peptodyssey** iOS app and stores it in the
de-identified `healthkit_*` tables.

Related: [`healthkit-storage.md`](healthkit-storage.md) (design + open decisions),
[`healthkit-schema.sql`](healthkit-schema.sql) (original standalone draft).

---

## What this is

| Piece | Location |
|-------|----------|
| Router (`POST`/`GET /healthkit/samples`) | `engine/healthkit/api.py` (mounted in `api.py`) |
| Ingest / read logic | `engine/healthkit/service.py` |
| Request models | `engine/healthkit/schemas.py` |
| DB access (Postgres↔SQLite switch) | `engine/healthkit/db.py` |
| Postgres schema (auto-applied) | `db/migrations/008_healthkit.sql` |
| SQLite schema (dev/tests) | `engine/healthkit/schema.sql` |
| Tests | `tests/test_healthkit.py` |

**Data model** (mirrors `docs/healthkit-schema.sql`): one wide `healthkit_samples`
table keyed by the device `HKSample.uuid`, so re-syncs are **idempotent**
(`ON CONFLICT (sample_uuid) DO NOTHING`). Subjects are an **opaque, app-assigned
`subject_id`** — no names/DOB/Apple id. Companion tables: `healthkit_workouts`,
`healthkit_sync_anchors`, `healthkit_ingestions` (audit), `healthkit_subjects`.

---

## 1. Run it locally

### With Docker (Postgres included)

```bash
cp .env.example .env          # DATABASE_URL defaults to the bundled `db` service
docker compose up --build
curl http://localhost:8000/health
```

The `db` service (`postgres:16-alpine`) is already in `docker-compose.yml`, and
the engine runs `db/migrate.py` on startup — so `008_healthkit.sql` creates the
tables automatically when `DATABASE_URL` is set.

### Without Docker

- **SQLite fallback (simplest):** leave `DATABASE_URL` unset. `engine/healthkit/db.py`
  falls back to `data/healthkit.db` and applies `engine/healthkit/schema.sql`
  automatically. Good for a quick run against the iOS Simulator.
- **Local Postgres:** point at any Postgres and apply the migration:

  ```bash
  export DATABASE_URL='postgresql://u4u:u4u_dev_password@localhost:5432/u4u'
  psql "$DATABASE_URL" -f db/migrations/008_healthkit.sql   # or let db/migrate.py do it on boot
  uvicorn api:app --reload
  ```

---

## 2. Send data (dev)

In dev there's no Authentik proxy, so `current_user` is `None` and ingestion is
accepted with `created_by`/`notes` unset (same soft-auth pattern as `/analyze`).

```bash
curl -X POST http://localhost:8000/healthkit/samples \
  -H 'Content-Type: application/json' \
  -d '{
        "subject_id": "subj_DEMO",
        "samples": [{
          "uuid": "11111111-1111-1111-1111-111111111111",
          "class": "quantity",
          "type": "HKQuantityTypeIdentifierHeartRate",
          "value": 72, "unit": "count/min",
          "start": "2026-07-03T12:00:00Z", "end": "2026-07-03T12:00:00Z",
          "source": {"name": "Apple Watch", "bundleId": "com.apple.health"},
          "device": {"name": "Watch"}, "metadata": {}
        }]
      }'
# → {"received":1,"inserted":1}   (re-send the same uuid → inserted:0)

curl 'http://localhost:8000/healthkit/samples?subject_id=subj_DEMO'
```

---

## 3. Authentication (Authentik)

The endpoint uses the engine's existing **Authentik forward-auth** dependency
(`engine/users/deps.py`): in prod the Authentik proxy stamps `X-authentik-*`
headers and the operator is recorded in the ingestion audit; in dev (no proxy)
it's `None` and ingestion still works. Health data stays de-identified — the
subject is the app-assigned `subject_id`, never the Authentik user.

**For the iOS app to authenticate in prod**, register an **OAuth2/OIDC
application** in Authentik with the **Device Code** grant enabled, then give the
app the **issuer URL** (`https://auth.<domain>/application/o/<slug>/`) and
**client ID**. The app does the device-code flow, stores the token in the
Keychain, and sends it as `Authorization: Bearer …` through the proxy. (App side:
Account → Authentik settings, "Sign in with Authentik".)

---

## 4. Configure the peptodyssey app

In the app's dashboard:

- **Backend → Base URL:** the API origin. Local: `http://<mac-ip>:8000`.
  Prod behind the `/api/v1/*` proxy: `https://<host>/api/v1` (the upload path
  `/healthkit/samples` is unprefixed on the server).
- **Account (Authentik):** issuer URL + client ID, then Sign in.
- `subject_id` is generated and stored on the device automatically.

---

## 5. Tests

```bash
pytest tests/test_healthkit.py       # SQLite; no Postgres required
```

Covers idempotency (re-sent uuid → `inserted:0`), read-back, workout rows, and
the audit row.

---

## 6. Production

Prod stores into the in-cluster Postgres (`u4u-postgres`, iac repo Flux
"theswamp"). Per [`healthkit-storage.md`](healthkit-storage.md) it's gated on the
`u4u-postgres-secret` **Bitwarden UUID** step — someone with Bitwarden + cluster
access must create the `u4u` login item and paste its UUID before the API pod
mounts `DATABASE_URL`. Once set, `db/migrate.py` applies `008_healthkit.sql` on
deploy. Confirm the IRB/data-scope posture in `healthkit-storage.md` before real
ingestion.
