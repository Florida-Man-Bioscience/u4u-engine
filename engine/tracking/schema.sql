-- engine/tracking/schema.sql
-- ===========================
-- SQLite schema for longitudinal biomarker tracking.
-- Lives in data/biomarker_tracking.db (path overridable via TRACKING_DB_PATH).
-- No PHI: patients are identified by an opaque label (e.g. "P-001"); no names,
-- DOB precision is capped at birth_year, and free-text notes are caller's
-- responsibility.

CREATE TABLE IF NOT EXISTS patients (
    id          TEXT PRIMARY KEY,
    label       TEXT NOT NULL,
    sex         TEXT,                   -- 'M' | 'F' | 'other' | NULL
    birth_year  INTEGER,
    notes       TEXT,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_patients_label ON patients(label);

CREATE TABLE IF NOT EXISTS treatments (
    id            TEXT PRIMARY KEY,
    patient_id    TEXT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    peptide_name  TEXT NOT NULL,        -- canonical name matching biomarkers.PEPTIDE_BIOMARKERS
    dose          REAL,
    dose_unit     TEXT,                 -- 'mg' | 'mcg' | 'IU' | …
    schedule      TEXT,                 -- 'QD' | 'BID' | '2x/week' | …
    route         TEXT,                 -- 'SC' | 'IM' | 'PO' | 'topical' | …
    start_date    TEXT NOT NULL,        -- ISO date (YYYY-MM-DD)
    end_date      TEXT,                 -- NULL = ongoing
    notes         TEXT,
    created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE INDEX IF NOT EXISTS idx_treatments_patient ON treatments(patient_id);
CREATE INDEX IF NOT EXISTS idx_treatments_peptide ON treatments(peptide_name);

CREATE TABLE IF NOT EXISTS measurements (
    id              TEXT PRIMARY KEY,
    patient_id      TEXT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    treatment_id    TEXT REFERENCES treatments(id) ON DELETE SET NULL,
    biomarker_name  TEXT NOT NULL,      -- matches BiomarkerMeasurement.name
    modality        TEXT,               -- denormalized for fast filtering
    value           REAL NOT NULL,
    unit            TEXT,
    measured_at     TEXT NOT NULL,      -- ISO datetime
    notes           TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE INDEX IF NOT EXISTS idx_measurements_patient    ON measurements(patient_id);
CREATE INDEX IF NOT EXISTS idx_measurements_treatment  ON measurements(treatment_id);
CREATE INDEX IF NOT EXISTS idx_measurements_biomarker  ON measurements(biomarker_name);
CREATE INDEX IF NOT EXISTS idx_measurements_at         ON measurements(measured_at);

-- ── Genetic profile (one row per patient) ───────────────────────────────────
-- profile_json: JSON-serialised GeneticProfile (see engine/tracking/genetics.py)
--   {
--     "variants": [{rsid, gene, genotype, peptide_effects: {peptide: weight}, ...}],
--     "generated_at": "...",
--     "source": "synthetic" | "uploaded"
--   }
CREATE TABLE IF NOT EXISTS patient_genetics (
    patient_id   TEXT PRIMARY KEY REFERENCES patients(id) ON DELETE CASCADE,
    profile_json TEXT NOT NULL,
    source       TEXT NOT NULL DEFAULT 'synthetic',
    created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
