-- db/migrations/008_healthkit.sql
-- ===============================
-- HealthKit ingestion tables (Postgres). Promoted from docs/healthkit-schema.sql
-- now that the destination is confirmed (the u4u Postgres). De-identified:
-- subjects are an opaque app-assigned id; no names / DOB / Apple health id.
-- Mirrors engine/healthkit/schema.sql (SQLite) one-for-one.

CREATE TABLE IF NOT EXISTS healthkit_subjects (
    id            TEXT PRIMARY KEY,
    label         TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS healthkit_samples (
    sample_uuid       UUID PRIMARY KEY,
    subject_id        TEXT NOT NULL REFERENCES healthkit_subjects(id) ON DELETE CASCADE,

    sample_class      TEXT NOT NULL,
    type_identifier   TEXT NOT NULL,

    value             DOUBLE PRECISION,
    unit              TEXT,

    start_time        TIMESTAMPTZ NOT NULL,
    end_time          TIMESTAMPTZ NOT NULL,

    source_name       TEXT,
    source_bundle_id  TEXT,
    device            JSONB,

    metadata          JSONB NOT NULL DEFAULT '{}'::jsonb,

    ingested_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hk_samples_subject     ON healthkit_samples(subject_id);
CREATE INDEX IF NOT EXISTS idx_hk_samples_type        ON healthkit_samples(type_identifier);
CREATE INDEX IF NOT EXISTS idx_hk_samples_start       ON healthkit_samples(start_time);
CREATE INDEX IF NOT EXISTS idx_hk_samples_subj_type_t ON healthkit_samples(subject_id, type_identifier, start_time);

CREATE TABLE IF NOT EXISTS healthkit_workouts (
    sample_uuid        UUID PRIMARY KEY REFERENCES healthkit_samples(sample_uuid) ON DELETE CASCADE,
    activity_type      TEXT,
    duration_s         DOUBLE PRECISION,
    total_energy_kcal  DOUBLE PRECISION,
    total_distance_m   DOUBLE PRECISION,
    metadata           JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS healthkit_sync_anchors (
    subject_id        TEXT NOT NULL REFERENCES healthkit_subjects(id) ON DELETE CASCADE,
    type_identifier   TEXT NOT NULL,
    anchor            TEXT NOT NULL,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (subject_id, type_identifier)
);

CREATE TABLE IF NOT EXISTS healthkit_ingestions (
    id                BIGSERIAL PRIMARY KEY,
    subject_id        TEXT NOT NULL REFERENCES healthkit_subjects(id) ON DELETE CASCADE,
    received_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sample_count      INTEGER NOT NULL,
    inserted_count    INTEGER NOT NULL,
    source_name       TEXT,
    notes             TEXT
);

CREATE INDEX IF NOT EXISTS idx_hk_ingestions_subject ON healthkit_ingestions(subject_id, received_at);
