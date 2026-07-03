-- db/migrations/009_healthkit_device_tokens.sql
-- =============================================
-- Interim per-device bearer tokens for the HealthKit ingestion endpoint, so
-- POST /healthkit/samples is not an open write endpoint in production. The raw
-- token is shown once at mint time (scripts/create_healthkit_token.py) and only
-- its SHA-256 hex is stored here. Mirrors engine/healthkit/schema.sql (SQLite).
--
-- Optional `subject_id` binding: when set, the token may only write that
-- subject; when NULL, it may write any subject_id.

CREATE TABLE IF NOT EXISTS healthkit_device_tokens (
    token_hash    CHAR(64)    PRIMARY KEY,   -- SHA-256 hex of the raw bearer token
    label         TEXT,                       -- human note, e.g. "Curtis iPhone"
    subject_id    TEXT,                       -- optional binding; NULL = any subject
    revoked       BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at  TIMESTAMPTZ
);
