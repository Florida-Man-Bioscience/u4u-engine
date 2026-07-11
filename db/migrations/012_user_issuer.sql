-- db/migrations/012_user_issuer.sql
-- ==================================
-- Distinguish identity populations sharing the users table: cluster-admin
-- Authentik (staff) vs the dedicated end-user Authentik. `issuer` is the OIDC
-- issuer URL; uniqueness moves from authentik_uid alone to (issuer, sub) so the
-- same subject id from two IdPs can't collide.
BEGIN;

ALTER TABLE users ADD COLUMN IF NOT EXISTS issuer TEXT;

-- Backfill existing rows: they all came from the cluster-admin Authentik.
UPDATE users
   SET issuer = COALESCE(NULLIF(current_setting('u4u.cluster_issuer', true), ''),
                         'cluster-authentik')
 WHERE issuer IS NULL;

ALTER TABLE users ALTER COLUMN issuer SET NOT NULL;

-- Lockstep with engine/users/schema.sql's `DEFAULT 'cluster-authentik'`
-- (SQLite fallback schema). All current insert paths supply `issuer`
-- explicitly so this is latent today, but keeps the two schemas aligned.
ALTER TABLE users ALTER COLUMN issuer SET DEFAULT 'cluster-authentik';

-- Replace the single-column uniqueness with the composite.
DROP INDEX IF EXISTS idx_users_authentik_uid;
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_issuer_uid ON users(issuer, authentik_uid);

COMMIT;
