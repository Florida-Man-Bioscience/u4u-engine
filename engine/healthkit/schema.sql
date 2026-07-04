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

-- Interim per-device bearer tokens (mirrors db/migrations/009_healthkit_device_tokens.sql).
-- Raw token shown once at mint; only its SHA-256 hex is stored. Optional
-- subject_id binding: NULL = may write any subject.
CREATE TABLE IF NOT EXISTS healthkit_device_tokens (
    token_hash    TEXT PRIMARY KEY,
    label         TEXT,
    subject_id    TEXT,
    revoked       INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    last_used_at  TEXT
);

-- Identity bridge: de-identified HealthKit subject_id ↔ tracking patient_id
-- (mirrors db/migrations/010_healthkit_subject_map.sql). No cross-file FKs:
-- in dev the healthkit and tracking tables live in separate SQLite files, so a
-- REFERENCES here would break inserts under PRAGMA foreign_keys=ON. Resolver:
-- engine/tracking/healthkit_identity.py.
CREATE TABLE IF NOT EXISTS healthkit_subject_map (
    subject_id  TEXT PRIMARY KEY,
    patient_id  TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE INDEX IF NOT EXISTS idx_hk_subject_map_patient ON healthkit_subject_map(patient_id);
