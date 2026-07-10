import pytest

from engine.users import db, get_conn


@pytest.fixture(autouse=True)
def isolated_users_db(tmp_path, monkeypatch):
    """Redirect the users default DB path to a per-test tmp file so
    tests in this directory (e.g. test_deps_auth.py, which goes through
    deps.required_user -> current_user -> db.get_conn() with no
    explicit path) never touch the real data/users.db.

    engine/users/db._DEFAULT_PATH is captured at module import time, so
    monkeypatch the attribute directly and reset the schema-init memo so
    the new file gets a fresh schema run. This does not affect the
    ``conn`` fixture below, which already bypasses the default path by
    passing ":memory:" explicitly.
    """
    monkeypatch.setattr(db, "_DEFAULT_PATH", tmp_path / "users.db")
    db.reset_initialized()
    yield
    db.reset_initialized()


@pytest.fixture
def conn():
    db.reset_initialized()
    with get_conn(":memory:") as c:
        yield c
