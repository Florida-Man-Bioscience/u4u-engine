-- db/migrations/001_initial_schema.sql
-- ======================================
-- Jobs, per-variant results, condition library, and job pipeline output.
-- Run once against a fresh database; safe to re-run (IF NOT EXISTS guards).

BEGIN;

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ── jobs ──────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS jobs (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    status              TEXT        NOT NULL DEFAULT 'pending'
                                    CHECK (status IN ('pending','running','done','failed')),

    filename            TEXT        NOT NULL,
    file_size_bytes     INT         NOT NULL,

    progress_step       TEXT,
    progress_pct        SMALLINT    DEFAULT 0,

    variant_count       INT,
    error_message       TEXT,

    -- Full pipeline output (variants, pgx_profile, dossiers, acmg_summary, etc.)
    -- Stored as JSONB for complete result retrieval and ACMG signoff updates.
    pipeline_output_json JSONB,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at          TIMESTAMPTZ,
    finished_at         TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_jobs_status     ON jobs (status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs (created_at DESC);

-- ── results ───────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS results (
    id                      BIGSERIAL   PRIMARY KEY,
    job_id                  UUID        NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,

    variant_id              TEXT        NOT NULL,
    rsid                    TEXT,
    location                TEXT,
    chrom                   TEXT,
    pos                     INT,
    ref                     TEXT,
    alt                     TEXT,
    zygosity                TEXT,

    consequence             TEXT,
    genes                   TEXT[],
    clinvar                 TEXT,
    clinvar_raw             TEXT,
    disease_name            TEXT,
    condition_key           TEXT,
    gnomad_af               DOUBLE PRECISION,
    gnomad_popmax           DOUBLE PRECISION,
    gnomad_homozygote_count INT,

    score                   INT         NOT NULL,
    tier                    TEXT        NOT NULL
                            CHECK (tier IN ('critical','high','medium','low')),
    reasons                 TEXT[],
    frequency_derived_label TEXT,
    carrier_note            TEXT,

    emoji                   TEXT,
    headline                TEXT,
    consequence_plain       TEXT,
    rarity_plain            TEXT,
    clinvar_plain           TEXT,
    action_hint             TEXT,
    zygosity_plain          TEXT,

    full_json               JSONB       NOT NULL,

    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_results_job_id        ON results (job_id);
CREATE INDEX IF NOT EXISTS idx_results_job_tier       ON results (job_id, tier);
CREATE INDEX IF NOT EXISTS idx_results_score          ON results (job_id, score DESC);
CREATE INDEX IF NOT EXISTS idx_results_condition_key  ON results (condition_key)
    WHERE condition_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_results_disease_trgm   ON results
    USING gin (disease_name gin_trgm_ops)
    WHERE disease_name IS NOT NULL;

-- ── condition_library ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS condition_library (
    condition_key       TEXT        PRIMARY KEY,
    display_name        TEXT        NOT NULL,
    gene_symbols        TEXT[],
    inheritance_pattern TEXT,
    acmg_sf             BOOLEAN     NOT NULL DEFAULT FALSE,
    category            TEXT,
    prevalence          TEXT,
    plain_description   TEXT,
    action_guidance     TEXT,
    carrier_note        TEXT,
    last_reviewed       DATE,
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ── Views ─────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW job_summary AS
SELECT
    j.id                                                AS job_id,
    j.status,
    j.filename,
    j.variant_count,
    j.created_at,
    j.finished_at,
    ROUND(EXTRACT(EPOCH FROM (j.finished_at - j.started_at))::NUMERIC, 1) AS runtime_seconds,
    COUNT(r.id) FILTER (WHERE r.tier = 'critical')      AS critical_count,
    COUNT(r.id) FILTER (WHERE r.tier = 'high')          AS high_count,
    COUNT(r.id) FILTER (WHERE r.tier = 'medium')        AS medium_count,
    COUNT(r.id) FILTER (WHERE r.tier = 'low')           AS low_count
FROM jobs j
LEFT JOIN results r ON r.job_id = j.id
GROUP BY j.id;

COMMIT;
