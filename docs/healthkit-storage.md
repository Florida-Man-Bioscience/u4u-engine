# HealthKit data storage — setup & design

Goal: give the iOS app a Postgres-backed place to store HealthKit data. This
doc covers what's wired up now, the proposed schema, and the decisions still
needed before real HealthKit data flows in.

> **A phone never talks to Postgres directly.** The iOS app should POST batches
> over HTTPS to an ingestion endpoint that writes to Postgres. "A Postgres
> server for HealthKit data" therefore means **schema + endpoint + database**,
> not an exposed `:5432`. The endpoint is sketched below but not yet built —
> see [Open decisions](#open-decisions).

## What's set up now (local dev)

`docker-compose.yml` now includes a `postgres:16-alpine` service and defaults
`DATABASE_URL` to it. It mirrors the production StatefulSet (db/user `u4u`) in
the iac repo (`rke2/tooling/flux/theswamp/postgres.yaml`).

```bash
cp .env.example .env          # fill NCBI_API_KEY (DATABASE_URL defaults to the pg service)
docker compose up --build
curl http://localhost:8000/health
```

The engine auto-runs `db/migrate.py` on startup and, with no `DATABASE_URL`,
falls back to SQLite — so removing the `postgres` service reverts cleanly.

Point `psql` (or a native iOS-simulator build) at it on the host:

```bash
psql "postgresql://u4u:u4u_dev_password@localhost:5432/u4u"
```

## Proposed schema

[`docs/healthkit-schema.sql`](healthkit-schema.sql) — a **standalone draft**, not
under `db/migrations/` (those auto-apply to the u4u study DB; whether HealthKit
belongs there is an open decision). Apply by hand against a dev DB:

```bash
psql "postgresql://u4u:u4u_dev_password@localhost:5432/u4u" -f docs/healthkit-schema.sql
```

Shape:

| Table | Holds |
|---|---|
| `healthkit_subjects` | Opaque subject id ↔ optional label. No names/DOB. |
| `healthkit_samples` | One row per HealthKit sample; keyed by device `HKSample.uuid` (idempotent re-sync). `type_identifier` + `value`/`unit` + `metadata` JSONB. |
| `healthkit_workouts` | Workout summary fields (activity, duration, energy, distance), 1:1 with a `sample_class='workout'` row. |
| `healthkit_sync_anchors` | Per-(subject, type) `HKAnchoredObjectQuery` anchor for incremental sync. |
| `healthkit_ingestions` | Audit row per upload batch. |

**Why a standalone schema, not the existing `measurements` table:** the
biomarker tracking schema (`engine/tracking/schema.sql`) is deliberately
PHI-free and peptide-biomarker-shaped for the observational study. Raw HealthKit
is broad (~100 sample types — HR, HRV, sleep, steps, ECG, workouts) and
identifiable. Folding it in would overload a study table and blur the study's
de-identified data model. A dedicated schema keeps them separate; a thin
mapping job can still project chosen HealthKit types (e.g. body mass, HbA1c)
into `measurements` later if the study wants them.

## Ingestion endpoint (sketch — not yet built)

Mirror the existing `engine/tracking/api.py` mount. The app sends anchored
deltas; the server upserts and returns the count:

```
POST /healthkit/samples
  Authorization: Bearer <token>        # same auth as the rest of the API
  { "subject_id": "...",
    "samples": [
      { "uuid": "…", "class": "quantity",
        "type": "HKQuantityTypeIdentifierHeartRate",
        "value": 62, "unit": "count/min",
        "start": "2026-07-03T12:00:00Z", "end": "2026-07-03T12:00:00Z",
        "source": {"name": "Apple Watch", "bundleId": "…"},
        "device": {…}, "metadata": {…} } ] }
  → { "received": N, "inserted": M }    # M < N when re-syncing (ON CONFLICT DO NOTHING)

GET  /healthkit/samples?subject_id=…&type=…&since=…   # read back a series
```

Idempotency comes from the `sample_uuid` primary key — safe to retry a failed
sync. On iOS use `HKAnchoredObjectQuery`, persist the returned anchor, and send
only deltas; the server can also mirror the anchor in `healthkit_sync_anchors`.

## Production path

The in-cluster Postgres (`u4u-postgres`, StatefulSet in the iac repo) is the
production home. Per [`docs/server-management.md`](server-management.md) it is
**blocked on a human step**: the `u4u-postgres-secret` ExternalSecret still has
`REPLACE_WITH_BITWARDEN_ITEM_UUID`. Someone with Bitwarden + cluster access must
create the `u4u` Login item and paste its UUID before the API pod can mount
`DATABASE_URL` in prod. That's independent of this local setup.

## Open decisions

1. **Standalone iOS backend, or part of the u4u platform?** Decides where the
   code, endpoint, and data live — and whether the schema becomes a numbered
   `db/migrations/` file in *this* DB or a separate database/service.
2. **Data scope + IRB/PHI.** The project is under active observational-study /
   IRB framing with a de-identified data model. "Store *all* the HealthKit
   data" is identifiable health data — a change to the data-collection posture.
   Confirm what's actually collected, how subjects are identified/consented,
   and that it's within the approved protocol before real ingestion is wired.
3. **Production DB provisioning** — the Bitwarden UUID step above.
