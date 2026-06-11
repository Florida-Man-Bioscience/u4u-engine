"""
engine/auth/service.py
======================
User and session CRUD. Plain functions over a sqlite3.Connection so they
compose with the existing tracking-style services and are easy to test
with an in-memory DB.

Password hashing uses bcrypt (cost factor 12 — bcrypt's default). Session
tokens are 256 bits of os.urandom encoded as URL-safe base64 — opaque
to the client and to the DB, validated only by lookup.
"""
from __future__ import annotations

import os
import secrets
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt

# 7-day token lifetime. Tunable via env if anyone ever needs to.
SESSION_TTL_DAYS = int(os.getenv("AUTH_SESSION_TTL_DAYS", "7"))

# Pre-computed valid bcrypt hash of a random string. Used as a target for
# verify_password() when the username is unknown so the work factor (~50ms)
# is paid regardless — closing the obvious timing channel that would
# otherwise leak which usernames exist.
_DUMMY_HASH = bcrypt.hashpw(secrets.token_bytes(16), bcrypt.gensalt()).decode("utf-8")


class AuthError(Exception):
    """Raised by authenticate() on bad credentials. Always 401-shaped."""


@dataclass(frozen=True)
class User:
    id: str
    username: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "username": self.username, "created_at": self.created_at}


@dataclass(frozen=True)
class Session:
    token: str
    user_id: str
    created_at: str
    expires_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "token": self.token,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }


# ── Password hashing ────────────────────────────────────────────────────────

def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, stored_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), stored_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ── Users ───────────────────────────────────────────────────────────────────

def create_user(conn: sqlite3.Connection, *, username: str, password: str) -> User:
    """Create a new user. Raises sqlite3.IntegrityError on duplicate username."""
    uid = str(uuid.uuid4())
    pw_hash = _hash_password(password)
    conn.execute(
        "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
        (uid, username, pw_hash),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id, username, created_at FROM users WHERE id = ?", (uid,)
    ).fetchone()
    return User(id=row["id"], username=row["username"], created_at=row["created_at"])


def get_user_by_username(conn: sqlite3.Connection, username: str) -> User | None:
    row = conn.execute(
        "SELECT id, username, created_at FROM users WHERE username = ?", (username,)
    ).fetchone()
    if row is None:
        return None
    return User(id=row["id"], username=row["username"], created_at=row["created_at"])


def count_users(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]


# ── Authentication + sessions ───────────────────────────────────────────────

def authenticate(conn: sqlite3.Connection, *, username: str, password: str) -> User:
    """Verify credentials. Raises AuthError on failure."""
    row = conn.execute(
        "SELECT id, username, password_hash, created_at FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if row is None:
        # Run a dummy verify against a real bcrypt hash so the per-request
        # cost is paid regardless of whether the username exists. Closes
        # the easy timing channel for username enumeration.
        _verify_password(password, _DUMMY_HASH)
        raise AuthError("invalid credentials")
    if not _verify_password(password, row["password_hash"]):
        raise AuthError("invalid credentials")
    return User(id=row["id"], username=row["username"], created_at=row["created_at"])


def create_session(
    conn: sqlite3.Connection, *, user_id: str, ttl_days: int | None = None,
) -> Session:
    """Mint a new opaque session token for a user."""
    token = secrets.token_urlsafe(32)  # 256 bits of entropy
    ttl = ttl_days if ttl_days is not None else SESSION_TTL_DAYS
    expires_at = (datetime.now(timezone.utc) + timedelta(days=ttl)).isoformat()
    conn.execute(
        "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
        (token, user_id, expires_at),
    )
    conn.commit()
    row = conn.execute(
        "SELECT token, user_id, created_at, expires_at FROM sessions WHERE token = ?",
        (token,),
    ).fetchone()
    return Session(
        token=row["token"], user_id=row["user_id"],
        created_at=row["created_at"], expires_at=row["expires_at"],
    )


def get_session_user(conn: sqlite3.Connection, token: str) -> User | None:
    """Return the user behind a session token, or None if invalid/expired.

    Expired tokens are deleted as a side effect so the table doesn't grow
    forever even without an explicit purge task.
    """
    if not token:
        return None
    row = conn.execute(
        """SELECT s.expires_at AS expires_at,
                  u.id AS uid, u.username AS uname, u.created_at AS ucreated
           FROM sessions s
           JOIN users u ON u.id = s.user_id
           WHERE s.token = ?""",
        (token,),
    ).fetchone()
    if row is None:
        return None
    try:
        expires = datetime.fromisoformat(row["expires_at"])
    except ValueError:
        expires = None
    now = datetime.now(timezone.utc)
    if expires is None or expires < now:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        return None
    return User(id=row["uid"], username=row["uname"], created_at=row["ucreated"])


def revoke_session(conn: sqlite3.Connection, token: str) -> bool:
    cur = conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    return cur.rowcount > 0


def purge_expired_sessions(conn: sqlite3.Connection) -> int:
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
    conn.commit()
    return cur.rowcount


# ── Bootstrap ───────────────────────────────────────────────────────────────

def bootstrap_admin(conn: sqlite3.Connection) -> User | None:
    """Create an initial admin user from env vars if the users table is empty.

    Seed-only-on-empty by design: subsequent edits to the env vars are
    ignored so an operator with deploy access can't silently rotate the
    password and take over a live account. To change credentials, log in
    and use the (future) password-change endpoint, or wipe ``data/auth.db``.
    """
    username = os.getenv("AUTH_BOOTSTRAP_USERNAME", "").strip()
    password = os.getenv("AUTH_BOOTSTRAP_PASSWORD", "")
    if not username or not password:
        return None
    if count_users(conn) > 0:
        return None
    return create_user(conn, username=username, password=password)
