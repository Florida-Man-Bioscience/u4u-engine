# HealthKit ingestion — setup

How to run and configure the `POST /healthkit/samples` endpoint that receives
Apple HealthKit data from the **peptodyssey** iOS app and stores it in the
de-identified `healthkit_*` tables.

Related: [`healthkit-storage.md`](healthkit-storage.md) (design, schema & auth).

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

**Data model** (`db/migrations/008_healthkit.sql`): one wide `healthkit_samples`
table keyed by the device `HKSample.uuid`, so re-syncs are **idempotent**
(`ON CONFLICT (sample_uuid) DO NOTHING`). Subjects are an **opaque, app-assigned
`subject_id`** — no names/DOB/Apple id. Companion tables: `healthkit_workouts`,
`healthkit_sync_anchors`, `healthkit_ingestions` (audit), `healthkit_subjects`.

---

## 1. Run it locally

### With Docker (Postgres included)

```bash
cp .env.example .env          # DATABASE_URL defaults to the bundled `postgres` service
docker compose up --build
curl http://localhost:8000/health
```

The `postgres` service (`postgres:16-alpine`) is already in `docker-compose.yml`, and
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

## 2. Send data

Ingestion requires a per-device bearer token whenever a real database is
configured (prod, or `HEALTHKIT_REQUIRE_TOKEN=1`). Mint one and send it as
`Authorization: Bearer <token>`:

```bash
python scripts/create_healthkit_token.py --label "dev laptop"   # prints the raw token once
```

The local SQLite dev fallback (no `DATABASE_URL`) is open, so the header is
optional there; against Postgres it is required (a token-less call gets `401`).

```bash
curl -X POST http://localhost:8000/healthkit/samples \
  -H 'Authorization: Bearer <token>' \
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

# reads require a subject-BOUND token (mint with --subject subj_DEMO):
curl 'http://localhost:8000/healthkit/samples?subject_id=subj_DEMO' \
  -H 'Authorization: Bearer <token bound to subj_DEMO>'
```

---

## 3. Authentication

**Current: per-device bearer token** (`engine/healthkit/auth.py`). Mint with
`scripts/create_healthkit_token.py` (optionally `--subject <id>` to bind it), send
it as `Authorization: Bearer <token>`. Required whenever `DATABASE_URL` is set
(prod) — no env var opens a Postgres-backed deployment; the local SQLite fallback
is open unless `HEALTHKIT_REQUIRE_TOKEN=1`. A bound token may only touch its
subject, and `GET` requires a bound token. Health data stays de-identified — the
subject is the app-assigned `subject_id`, never an Authentik user. `current_user`
(Authentik headers) is recorded in the audit when a proxy is present, but does
not gate the request.

**Target: Authentik** (forward-auth or OAuth2 device-code flow) — see
[`healthkit-storage.md`](healthkit-storage.md#authentication). Register an OAuth2
application with the Device Code grant, give the app the issuer URL + client ID;
the app does the device-code flow and sends the resulting token as a bearer.

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
