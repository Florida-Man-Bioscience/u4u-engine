-- db/migrations/008_healthkit_ingestion.sql
-- ==========================================
-- HealthKit ingestion tables for the peptodyssey iOS app.
-- Apply once against the Postgres database:
--   psql $DATABASE_URL -f db/migrations/008_healthkit_ingestion.sql
--
-- Mirrors engine/health/models.py. The API also create_all()s these on boot
-- when DATABASE_URL is set, so this file is primarily for production/manual use.
--
-- NOTE: the iOS app's end-users live in `app_users`, a SEPARATE table from the
-- platform's `users` (Authentik-backed operators, migration 004_users.sql).
-- They are distinct populations; do not merge them.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()

-- ── app_users ─────────────────────────────────────────────────────────────────
-- One row per peptodyssey app account (email identity for now). Distinct from
-- the operator `users` table created by 004_users.sql.
CREATE TABLE IF NOT EXISTS app_users (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT        NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── device_tokens ─────────────────────────────────────────────────────────────
-- Long-lived opaque bearer tokens, stored as SHA-256 hex. The raw token is
-- shown once at creation (scripts/create_device_token.py).
CREATE TABLE IF NOT EXISTS device_tokens (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID        NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    token_hash   CHAR(64)    NOT NULL UNIQUE,
    device_name  TEXT,
    revoked      BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_device_tokens_user ON device_tokens (user_id);

-- ── health_samples ────────────────────────────────────────────────────────────
-- One row per HealthKit sample. Composite PK (user_id, uuid) makes re-delivered
-- samples an idempotent upsert (the client is at-least-once).
CREATE TABLE IF NOT EXISTS health_samples (
    user_id                  UUID        NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    uuid                     UUID        NOT NULL,

    type_identifier          TEXT        NOT NULL,
    kind                     TEXT        NOT NULL,

    start_date               TIMESTAMPTZ NOT NULL,
    end_date                 TIMESTAMPTZ NOT NULL,

    value                    DOUBLE PRECISION,
    unit                     TEXT,
    category_value           INTEGER,

    source_name              TEXT,
    source_bundle_identifier TEXT,
    device_name              TEXT,

    workout                  JSONB,
    sample_metadata          JSONB,

    is_deleted               BOOLEAN     NOT NULL DEFAULT FALSE,
    received_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (user_id, uuid)
);

CREATE INDEX IF NOT EXISTS idx_health_samples_user_type
    ON health_samples (user_id, type_identifier);
CREATE INDEX IF NOT EXISTS idx_health_samples_user_end
    ON health_samples (user_id, end_date DESC);
CREATE INDEX IF NOT EXISTS idx_health_samples_received
    ON health_samples (received_at DESC);

COMMENT ON TABLE health_samples IS
    'One row per HealthKit sample uploaded by the peptodyssey app. Mirrors the
     app''s PendingSamplePayload. Upserted by (user_id, uuid).';
