-- db/migrations/005_ownership_fks.sql
-- ====================================
-- Wires app-user ownership into the existing domain tables.
--
-- 004 created the users anchor and explicitly deferred ownership FKs to
-- a later migration (see 004 prologue). This is that migration.
--
-- Columns are nullable forever — not just for backfill. Two callers
-- legitimately write NULL:
--   1. Existing rows from before this migration.
--   2. Dev-mode writes when the Authentik proxy isn't in front of the
--      api (npm run dev, local pytest). Inventing a synthetic system
--      user there would lie about provenance.
--
-- Idempotent on re-run: every ALTER uses ADD COLUMN IF NOT EXISTS and
-- every index uses CREATE INDEX IF NOT EXISTS.

BEGIN;

-- ── jobs ──────────────────────────────────────────────────────────────────────
ALTER TABLE jobs
    ADD COLUMN IF NOT EXISTS created_by_user_id UUID REFERENCES users(id);

CREATE INDEX IF NOT EXISTS idx_jobs_created_by ON jobs(created_by_user_id);

-- ── tracking ──────────────────────────────────────────────────────────────────
ALTER TABLE patients
    ADD COLUMN IF NOT EXISTS created_by_user_id UUID REFERENCES users(id);

ALTER TABLE treatments
    ADD COLUMN IF NOT EXISTS created_by_user_id UUID REFERENCES users(id);

ALTER TABLE measurements
    ADD COLUMN IF NOT EXISTS created_by_user_id UUID REFERENCES users(id);

CREATE INDEX IF NOT EXISTS idx_patients_created_by     ON patients(created_by_user_id);
CREATE INDEX IF NOT EXISTS idx_treatments_created_by   ON treatments(created_by_user_id);
CREATE INDEX IF NOT EXISTS idx_measurements_created_by ON measurements(created_by_user_id);

COMMIT;
