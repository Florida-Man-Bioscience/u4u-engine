-- docs/healthkit-schema.sql
-- ==========================
-- PROPOSED standalone schema for storing Apple HealthKit data synced from an
-- iOS app. Postgres dialect.
--
-- STATUS: draft / not wired in. This file is intentionally NOT under
-- db/migrations/ — files there auto-apply to the u4u study database on startup
-- (see db/migrate.py). Whether HealthKit data belongs in that same database is
-- an open scope + IRB decision (see docs/healthkit-storage.md). Apply this by
-- hand against a dev database, or promote it to a numbered migration once the
-- destination is confirmed:
--   psql "$DATABASE_URL" -f docs/healthkit-schema.sql
--
-- Design notes
-- ------------
-- * HealthKit exposes ~100 sample types across a few classes (quantity,
--   category, workout, correlation, clinical). Rather than a table per type,
--   this uses one wide `healthkit_samples` table keyed by the HealthKit type
--   identifier string, with a `metadata` JSONB column for the per-type extras.
-- * De-duplication is on the device-provided sample UUID (HKSample.uuid).
--   Re-syncs and HKAnchoredObjectQuery replays re-send the same samples; the
--   UNIQUE constraint + ON CONFLICT DO NOTHING makes ingestion idempotent.
-- * Subjects are identified by an opaque id only — matching the de-identified
--   posture of engine/tracking/schema.sql. No names / DOB / raw Apple health id.

CREATE TABLE IF NOT EXISTS healthkit_subjects (
    id            TEXT PRIMARY KEY,          -- opaque subject id (app-assigned)
    label         TEXT,                      -- optional human-facing label, e.g. "P-001"
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- One row per HealthKit sample.
CREATE TABLE IF NOT EXISTS healthkit_samples (
    -- HKSample.uuid from the device. Present for essentially all samples and
    -- stable across syncs, so it is the natural idempotency key.
    sample_uuid       UUID PRIMARY KEY,
    subject_id        TEXT NOT NULL REFERENCES healthkit_subjects(id) ON DELETE CASCADE,

    -- 'quantity' | 'category' | 'workout' | 'correlation' | 'clinical'
    sample_class      TEXT NOT NULL,
    -- HealthKit identifier string, e.g. 'HKQuantityTypeIdentifierHeartRate',
    -- 'HKCategoryTypeIdentifierSleepAnalysis'.
    type_identifier   TEXT NOT NULL,

    -- Quantity samples: the numeric reading in `unit`.
    -- Category samples: the enum raw value cast to numeric (unit NULL).
    value             DOUBLE PRECISION,
    unit              TEXT,                  -- HKUnit string, e.g. 'count/min', 'kg', 'mg/dL'

    start_time        TIMESTAMPTZ NOT NULL,
    end_time          TIMESTAMPTZ NOT NULL,  -- == start_time for instantaneous samples

    -- Provenance (HKSource / HKSourceRevision / HKDevice).
    source_name       TEXT,                  -- e.g. 'Apple Watch', 'MyApp'
    source_bundle_id  TEXT,                  -- e.g. 'com.apple.health.<uuid>'
    device            JSONB,                 -- {name, manufacturer, model, hardware, software}

    -- HKMetadata dictionary + any per-type extras (e.g. sleep stage, workout ref).
    metadata          JSONB NOT NULL DEFAULT '{}'::jsonb,

    ingested_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hk_samples_subject     ON healthkit_samples(subject_id);
CREATE INDEX IF NOT EXISTS idx_hk_samples_type        ON healthkit_samples(type_identifier);
CREATE INDEX IF NOT EXISTS idx_hk_samples_start       ON healthkit_samples(start_time);
-- Common query: one subject's readings of one type over a time window.
CREATE INDEX IF NOT EXISTS idx_hk_samples_subj_type_t ON healthkit_samples(subject_id, type_identifier, start_time);

-- Workouts carry richer summary fields than a plain quantity sample. The base
-- row still lives in healthkit_samples (sample_class='workout'); this table
-- holds the workout-specific summary, linked 1:1 by sample_uuid.
CREATE TABLE IF NOT EXISTS healthkit_workouts (
    sample_uuid           UUID PRIMARY KEY REFERENCES healthkit_samples(sample_uuid) ON DELETE CASCADE,
    activity_type         TEXT,              -- HKWorkoutActivityType, e.g. 'running'
    duration_s            DOUBLE PRECISION,  -- seconds
    total_energy_kcal     DOUBLE PRECISION,
    total_distance_m      DOUBLE PRECISION,
    metadata              JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- Server-side sync state for incremental HKAnchoredObjectQuery ingestion.
-- The iOS app persists an opaque anchor per sample type; storing the anchor
-- server-side too lets the backend detect gaps / resume, one row per
-- (subject, type).
CREATE TABLE IF NOT EXISTS healthkit_sync_anchors (
    subject_id        TEXT NOT NULL REFERENCES healthkit_subjects(id) ON DELETE CASCADE,
    type_identifier   TEXT NOT NULL,
    anchor            TEXT NOT NULL,         -- base64 HKQueryAnchor round-tripped from the client
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (subject_id, type_identifier)
);

-- Audit log of each batch upload from a device (one row per sync POST).
-- Useful for debugging dropped/duplicate syncs and for a coarse ingestion rate.
CREATE TABLE IF NOT EXISTS healthkit_ingestions (
    id                BIGSERIAL PRIMARY KEY,
    subject_id        TEXT NOT NULL REFERENCES healthkit_subjects(id) ON DELETE CASCADE,
    received_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sample_count      INTEGER NOT NULL,      -- samples in the batch
    inserted_count    INTEGER NOT NULL,      -- new rows (excludes ON CONFLICT skips)
    source_name       TEXT,
    notes             TEXT
);

CREATE INDEX IF NOT EXISTS idx_hk_ingestions_subject ON healthkit_ingestions(subject_id, received_at);
