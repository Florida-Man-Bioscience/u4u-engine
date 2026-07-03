-- db/migrations/002_caches_and_tracking.sql
-- ===========================================
-- Annotation cache, rsID resolver cache, and longitudinal biomarker
-- tracking tables. All ported from their respective SQLite schemas.

BEGIN;

-- ── Annotation cache (engine/annotators/cache.py) ────────────────────────────

CREATE TABLE IF NOT EXISTS annotation_cache (
    source      TEXT NOT NULL,
    lookup_key  TEXT NOT NULL,
    result_json TEXT,
    PRIMARY KEY (source, lookup_key)
);

-- ── rsID resolver cache (engine/rsid_resolver.py) ────────────────────────────

CREATE TABLE IF NOT EXISTS rsid_cache (
    rsid        TEXT NOT NULL,
    genotype    TEXT NOT NULL DEFAULT '',
    result_json TEXT,
    PRIMARY KEY (rsid, genotype)
);

-- ── Biomarker tracking (engine/tracking/) ────────────────────────────────────

CREATE TABLE IF NOT EXISTS patients (
    id          TEXT        PRIMARY KEY,
    label       TEXT        NOT NULL,
    sex         TEXT,
    birth_year  INTEGER,
    notes       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_patients_label ON patients(label);

CREATE TABLE IF NOT EXISTS treatments (
    id            TEXT        PRIMARY KEY,
    patient_id    TEXT        NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    peptide_name  TEXT        NOT NULL,
    dose          DOUBLE PRECISION,
    dose_unit     TEXT,
    schedule      TEXT,
    route         TEXT,
    start_date    TEXT        NOT NULL,
    end_date      TEXT,
    notes         TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_treatments_patient ON treatments(patient_id);
CREATE INDEX IF NOT EXISTS idx_treatments_peptide ON treatments(peptide_name);

CREATE TABLE IF NOT EXISTS measurements (
    id              TEXT        PRIMARY KEY,
    patient_id      TEXT        NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    treatment_id    TEXT        REFERENCES treatments(id) ON DELETE SET NULL,
    biomarker_name  TEXT        NOT NULL,
    modality        TEXT,
    value           DOUBLE PRECISION NOT NULL,
    unit            TEXT,
    measured_at     TEXT        NOT NULL,
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_measurements_patient   ON measurements(patient_id);
CREATE INDEX IF NOT EXISTS idx_measurements_treatment ON measurements(treatment_id);
CREATE INDEX IF NOT EXISTS idx_measurements_biomarker ON measurements(biomarker_name);
CREATE INDEX IF NOT EXISTS idx_measurements_at        ON measurements(measured_at);

CREATE TABLE IF NOT EXISTS patient_genetics (
    patient_id   TEXT        PRIMARY KEY REFERENCES patients(id) ON DELETE CASCADE,
    profile_json TEXT        NOT NULL,
    source       TEXT        NOT NULL DEFAULT 'synthetic',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMIT;
