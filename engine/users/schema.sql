-- engine/users/schema.sql
-- ========================
-- SQLite fallback schema for app user accounts. Mirrors
-- db/migrations/004_users.sql one-for-one — keep them in lockstep when
-- adding columns.

CREATE TABLE IF NOT EXISTS users (
    -- TEXT here (not UUID) because SQLite has no native UUID type;
    -- the service layer generates a uuid4 hex string at insert time
    -- so prod (Postgres uuid) and dev (sqlite text) round-trip the
    -- same value.
    id              TEXT        PRIMARY KEY,

    authentik_uid   TEXT        NOT NULL,
    username        TEXT        NOT NULL,
    email           TEXT,
    full_name       TEXT,
    groups          TEXT,
    issuer          TEXT        NOT NULL DEFAULT 'cluster-authentik',

    created_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    last_seen_at    TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    disabled_at     TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_issuer_uid ON users(issuer, authentik_uid);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
