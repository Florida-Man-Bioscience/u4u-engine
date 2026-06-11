-- engine/auth/schema.sql
-- ======================
-- SQLite schema for the username/password auth subsystem. Lives in
-- data/auth.db by default (path overridable via AUTH_DB_PATH).
--
-- One row per user. ``password_hash`` is a bcrypt hash string — never
-- store plaintext passwords. ``sessions`` are opaque tokens issued by
-- /auth/login; tokens are validated by lookup, not by signing, so
-- revoking a token means deleting its row.

CREATE TABLE IF NOT EXISTS users (
    id             TEXT PRIMARY KEY,
    username       TEXT NOT NULL,
    password_hash  TEXT NOT NULL,
    created_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username);

CREATE TABLE IF NOT EXISTS sessions (
    token       TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    expires_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
