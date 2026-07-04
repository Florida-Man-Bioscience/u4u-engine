-- db/migrations/010_healthkit_subject_map.sql
-- ============================================
-- Identity bridge between a de-identified HealthKit subject_id and a tracking
-- patient_id. This is the seam the unified peptide-effect model will use to
-- pull HealthKit-derived proxy observations / behavioural covariates into a
-- patient's prediction — but NO prediction wiring exists yet (Phase 0). This
-- migration only creates the map + lets the resolver round-trip.
--
-- De-identified: subject_id is the opaque app-assigned HealthKit id; patient_id
-- is the opaque tracking id. No PHI. No FKs declared here so the map stays
-- symmetric with the SQLite mirror (engine/healthkit/schema.sql), where the two
-- sides live in separate database files.
--
-- Mirrors engine/healthkit/schema.sql one-for-one — keep them in lockstep.

CREATE TABLE IF NOT EXISTS healthkit_subject_map (
    subject_id  TEXT PRIMARY KEY,
    patient_id  TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hk_subject_map_patient ON healthkit_subject_map(patient_id);
