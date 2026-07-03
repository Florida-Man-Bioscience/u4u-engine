# Deploying the HealthKit backend on Render

The engine ships a `render.yaml` Blueprint that stands up a managed Postgres and
the API (from the existing `Dockerfile`) with `DATABASE_URL` wired between them.

## 1. Create the Blueprint

1. Push a branch containing `render.yaml` (this file lives on `feat/healthkit-ingestion`).
2. In Render: **New → Blueprint**, select this repo/branch, apply.
   Render creates:
   - `u4u-db` — managed Postgres
   - `u4u-engine` — Docker web service, health-checked at `/health`

`engine/health/db.py` normalizes Render's `postgres://…` connection string into
`postgresql+asyncpg://…`, so no manual URL editing is needed.

## 2. Initialize the schema

The API runs `create_all` on boot when `DATABASE_URL` is set, so tables appear on
first start. To apply the canonical schema explicitly, use the Render shell (or
your local machine with the **External** database URL):

```bash
psql "$DATABASE_URL" -f db/migrations/004_healthkit_ingestion.sql
```

## 3. Mint a device token for a tester

Run against the **External** database URL (from the Render db page). The engine
must be importable, so install deps or run inside the image:

```bash
DATABASE_URL='postgresql+asyncpg://…external…' \
  python scripts/create_device_token.py tester@example.com --device "Curtis iPhone"
```

Copy the printed `pep_…` token (shown once).

## 4. Point the app at it

In peptodyssey → **Backend**:
- **Base URL:** `https://u4u-engine.onrender.com`
- **Token:** the `pep_…` value

The app posts to `POST /health-samples`. Verify:

```bash
curl -s https://u4u-engine.onrender.com/health          # liveness
curl -s -H "Authorization: Bearer pep_…" \
     https://u4u-engine.onrender.com/health-samples/summary
```

## Notes

- **Plans:** `render.yaml` uses `basic-256mb` (db) and `starter` (web). Adjust in
  the dashboard; the free Postgres tier expires after 90 days.
- **Secrets** (`NCBI_API_KEY`, `JOB_STORE_KEY`, `ALLOWED_ORIGINS`) are marked
  `sync: false` — set them in the dashboard, never in git.
- **Production prefix:** if you later front this with the `/api/v1/*` proxy the
  compose file describes, set the app's Base URL to `https://host/api/v1` — the
  app's upload path is unprefixed (`/health-samples`).
