-- db/migrations/007_cache_ttl.sql
-- ================================
-- Adds fetched_at to annotation_cache and rsid_cache so the application
-- can evict entries older than the upstream refresh cadence.
--
-- ClinVar / gnomAD / dbSNP refresh roughly monthly. Application code
-- evicts rows older than 90 days on the next put() to a given table,
-- which covers two refresh cycles without a scheduled job.
--
-- Existing rows get NOW() so they stay valid for 90 days from this
-- migration's run and then age out naturally — no big-bang eviction.
--
-- Idempotent: ADD COLUMN IF NOT EXISTS + CREATE INDEX IF NOT EXISTS.

BEGIN;

ALTER TABLE annotation_cache
    ADD COLUMN IF NOT EXISTS fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

ALTER TABLE rsid_cache
    ADD COLUMN IF NOT EXISTS fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_annotation_cache_fetched_at
    ON annotation_cache(fetched_at);

CREATE INDEX IF NOT EXISTS idx_rsid_cache_fetched_at
    ON rsid_cache(fetched_at);

COMMIT;
