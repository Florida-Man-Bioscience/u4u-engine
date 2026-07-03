-- db/migrations/006_regulatory_cache.sql
-- ========================================
-- TTL-aware cache for live regulatory source results (Regulations.gov,
-- ClinicalTrials.gov, openFDA, Federal Register).
--
-- Until now this lived only in the SQLite annotation_cache.db file —
-- even when the rest of the app was running on Postgres. That meant
-- prod deploys silently maintained a stray SQLite file holding the
-- regulatory hot path. Migration 006 brings the cache into Postgres so
-- prod has one storage backend.
--
-- TTL semantics: each row carries the wall-clock time it was fetched,
-- and the application compares it against the per-source TTL on every
-- read. Old rows aren't evicted on schedule — they're overwritten on
-- the next live fetch, and the index on fetched_at supports cheap
-- "what's stale?" probes if a cleanup job ever wants to sweep.
--
-- Idempotent: IF NOT EXISTS guards throughout.

BEGIN;

CREATE TABLE IF NOT EXISTS regulatory_cache (
    source      TEXT        NOT NULL,
    lookup_key  TEXT        NOT NULL,
    result_json TEXT,
    fetched_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (source, lookup_key)
);

CREATE INDEX IF NOT EXISTS idx_regulatory_cache_fetched_at
    ON regulatory_cache(fetched_at);

COMMIT;
