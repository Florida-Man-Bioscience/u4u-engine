-- db/migrations/004_users.sql
-- ============================
-- App user accounts (the human operators of the engine, not the
-- patients being tracked).
--
-- The deploy stack puts an Authentik forward-auth proxy in front of
-- the app (see docs/deploy.md). Authentik sends a stable subject id
-- in ``X-Authentik-Uid`` along with username/email/groups. The api
-- never sees a password — it just trusts the proxy did its job and
-- materialises a local row keyed off the subject id on first sight.
--
-- This table is the persistence anchor for everything that needs to
-- belong to a user: per-user patient ownership, audit logs of who
-- created/edited what, per-user preferences, etc. Those FKs land in
-- later migrations once the column names are settled — this migration
-- just creates the base row so they have something to reference.
--
-- Idempotent on re-run: every object guards with IF NOT EXISTS.

BEGIN;

CREATE TABLE IF NOT EXISTS users (
    -- Internal row id. UUID, not the Authentik uid — keeps the foreign
    -- key target stable even if the IdP swap happens later and we
    -- have to remap subjects.
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Stable subject id from Authentik (`X-Authentik-Uid` header).
    -- Unique so re-logins from the same SSO identity map to the same
    -- row.
    authentik_uid   TEXT        NOT NULL,

    -- Human-facing identifiers. Username is required (Authentik always
    -- sets it); email and full name are best-effort because Authentik
    -- only forwards them when the user has populated their profile.
    username        TEXT        NOT NULL,
    email           TEXT,
    full_name       TEXT,

    -- Comma-separated Authentik group memberships at last sight.
    -- Stored verbatim so the app doesn't have to maintain its own
    -- group catalog; queries that need RBAC join on substring or
    -- promote this to a proper table when scale demands it.
    groups          TEXT,

    -- Audit timestamps.
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Soft delete: when an operator leaves the team, set this and
    -- leave their historical records intact rather than nulling out
    -- FKs from patients/measurements they created.
    disabled_at     TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_authentik_uid ON users(authentik_uid);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

COMMIT;
