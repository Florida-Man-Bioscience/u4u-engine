"""
Tests for engine/auth/service.py — pure CRUD + session lifecycle.
Exercised against an in-memory SQLite DB so the test suite stays hermetic.
"""
import os
import sqlite3
import time

import pytest

from engine.auth import db as auth_db
from engine.auth import service as auth_service


@pytest.fixture
def conn():
    """Fresh in-memory auth DB per test."""
    auth_db.reset_initialized()
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    auth_db._ensure_schema(c, ":memory:")
    yield c
    c.close()


def test_create_user_and_lookup(conn):
    user = auth_service.create_user(conn, username="alice", password="hunter2")
    assert user.username == "alice"
    looked_up = auth_service.get_user_by_username(conn, "alice")
    assert looked_up is not None and looked_up.id == user.id


def test_duplicate_username_rejected(conn):
    auth_service.create_user(conn, username="alice", password="x")
    with pytest.raises(sqlite3.IntegrityError):
        auth_service.create_user(conn, username="alice", password="y")


def test_authenticate_accepts_correct_password(conn):
    auth_service.create_user(conn, username="alice", password="hunter2")
    user = auth_service.authenticate(conn, username="alice", password="hunter2")
    assert user.username == "alice"


def test_authenticate_rejects_wrong_password(conn):
    auth_service.create_user(conn, username="alice", password="hunter2")
    with pytest.raises(auth_service.AuthError):
        auth_service.authenticate(conn, username="alice", password="wrong")


def test_authenticate_rejects_unknown_username(conn):
    with pytest.raises(auth_service.AuthError):
        auth_service.authenticate(conn, username="nobody", password="hunter2")


def test_session_round_trip(conn):
    user = auth_service.create_user(conn, username="alice", password="hunter2")
    session = auth_service.create_session(conn, user_id=user.id)
    assert session.token
    looked_up = auth_service.get_session_user(conn, session.token)
    assert looked_up is not None and looked_up.id == user.id


def test_revoked_session_no_longer_valid(conn):
    user = auth_service.create_user(conn, username="alice", password="x")
    session = auth_service.create_session(conn, user_id=user.id)
    assert auth_service.revoke_session(conn, session.token) is True
    assert auth_service.get_session_user(conn, session.token) is None


def test_expired_session_is_purged_on_lookup(conn):
    user = auth_service.create_user(conn, username="alice", password="x")
    # ttl_days=0 → already expired by the time we look it up.
    session = auth_service.create_session(conn, user_id=user.id, ttl_days=0)
    time.sleep(0.01)
    assert auth_service.get_session_user(conn, session.token) is None
    # Row should have been deleted, not just rejected.
    row = conn.execute(
        "SELECT 1 FROM sessions WHERE token = ?", (session.token,)
    ).fetchone()
    assert row is None


def test_get_session_user_with_empty_token(conn):
    assert auth_service.get_session_user(conn, "") is None


def test_bootstrap_admin_seeds_on_empty(monkeypatch, conn):
    monkeypatch.setenv("AUTH_BOOTSTRAP_USERNAME", "admin")
    monkeypatch.setenv("AUTH_BOOTSTRAP_PASSWORD", "first-password")
    seeded = auth_service.bootstrap_admin(conn)
    assert seeded is not None and seeded.username == "admin"
    # Verify the password actually works.
    user = auth_service.authenticate(conn, username="admin", password="first-password")
    assert user.id == seeded.id


def test_bootstrap_admin_is_no_op_when_users_exist(monkeypatch, conn):
    auth_service.create_user(conn, username="alice", password="hunter2")
    monkeypatch.setenv("AUTH_BOOTSTRAP_USERNAME", "admin")
    monkeypatch.setenv("AUTH_BOOTSTRAP_PASSWORD", "second-password")
    assert auth_service.bootstrap_admin(conn) is None
    # alice still authenticates; no admin was created.
    assert auth_service.get_user_by_username(conn, "admin") is None


def test_bootstrap_admin_skips_when_env_unset(monkeypatch, conn):
    monkeypatch.delenv("AUTH_BOOTSTRAP_USERNAME", raising=False)
    monkeypatch.delenv("AUTH_BOOTSTRAP_PASSWORD", raising=False)
    assert auth_service.bootstrap_admin(conn) is None


def test_authenticate_timing_does_not_short_circuit_on_unknown_user(conn):
    """Unknown usernames should still incur a verify_password call so the
    timing channel doesn't leak account existence. Best-effort sanity check."""
    auth_service.create_user(conn, username="alice", password="hunter2" * 4)
    t0 = time.perf_counter()
    with pytest.raises(auth_service.AuthError):
        auth_service.authenticate(conn, username="ghost", password="hunter2" * 4)
    unknown = time.perf_counter() - t0
    t0 = time.perf_counter()
    with pytest.raises(auth_service.AuthError):
        auth_service.authenticate(conn, username="alice", password="wrong" * 4)
    known = time.perf_counter() - t0
    # Allow generous slack; we're checking that unknown isn't ~0ms while
    # known is ~50ms (bcrypt cost). 5x ratio is the loose threshold.
    assert unknown > 0.001
    assert max(unknown, known) / min(unknown, known) < 10
