-- engine/healthkit/schema.sql
-- ===========================
-- SQLite fallback schema for HealthKit ingestion (dev/tests). Mirrors
-- db/migrations/008_healthkit.sql one-for-one — keep them in lockstep.
--
-- Design mirrors docs/healthkit-schema.sql: opaque, de-identified subject_id;
-- one wide healthkit_samples table keyed by the device HKSample.uuid so
-- re-syncs are idempotent (INSERT ... ON CONFLICT DO NOTHING). JSON columns are
-- TEXT here (JSONB in Postgres).

CREATE TABLE IF NOT EXISTS healthkit_subjects (
    id          TEXT PRIMARY KEY,
    label       TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS healthkit_samples (
    sample_uuid       TEXT PRIMARY KEY,
    subject_id        TEXT NOT NULL REFERENCES healthkit_subjects(id) ON DELETE CASCADE,

    sample_class      TEXT NOT NULL,   -- 'quantity'|'category'|'workout'|'correlation'|'characteristic'
    type_identifier   TEXT NOT NULL,   -- e.g. 'HKQuantityTypeIdentifierHeartRate'

    value             REAL,
    unit              TEXT,

    start_time        TEXT NOT NULL,   -- ISO-8601
    end_time          TEXT NOT NULL,   -- == start_time for instantaneous samples

    source_name       TEXT,
    source_bundle_id  TEXT,
    device            TEXT,            -- JSON

    metadata          TEXT NOT NULL DEFAULT '{}',  -- JSON

    ingested_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE INDEX IF NOT EXISTS idx_hk_samples_subject     ON healthkit_samples(subject_id);
CREATE INDEX IF NOT EXISTS idx_hk_samples_type        ON healthkit_samples(type_identifier);
CREATE INDEX IF NOT EXISTS idx_hk_samples_subj_type_t ON healthkit_samples(subject_id, type_identifier, start_time);

CREATE TABLE IF NOT EXISTS healthkit_workouts (
    sample_uuid        TEXT PRIMARY KEY REFERENCES healthkit_samples(sample_uuid) ON DELETE CASCADE,
    activity_type      TEXT,
    duration_s         REAL,
    total_energy_kcal  REAL,
    total_distance_m   REAL,
    metadata           TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS healthkit_sync_anchors (
    subject_id        TEXT NOT NULL REFERENCES healthkit_subjects(id) ON DELETE CASCADE,
    type_identifier   TEXT NOT NULL,
    anchor            TEXT NOT NULL,
    updated_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    PRIMARY KEY (subject_id, type_identifier)
);

CREATE TABLE IF NOT EXISTS healthkit_ingestions (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id        TEXT NOT NULL REFERENCES healthkit_subjects(id) ON DELETE CASCADE,
    received_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    sample_count      INTEGER NOT NULL,
    inserted_count    INTEGER NOT NULL,
    source_name       TEXT,
    notes             TEXT
);

CREATE INDEX IF NOT EXISTS idx_hk_ingestions_subject ON healthkit_ingestions(subject_id, received_at);
