import pytest

from engine.tracking import db, get_conn


@pytest.fixture
def conn():
    db.reset_initialized()
    with get_conn(":memory:") as c:
        yield c


@pytest.fixture(autouse=True)
def _isolate_dbs(tmp_path, monkeypatch):
    """Redirect BOTH the users default DB and the tracking default DB to
    per-test tmp files so tests in this directory that drive
    ``TestClient(api.app)`` — which resolves the caller via
    ``engine.users.deps.required_user``/``current_user`` (opens
    ``data/users.db``) and performs tracking ops (opens
    ``data/biomarker_tracking.db``) — never touch the real on-disk
    databases. Without this, running the tracking test suite pollutes
    ``data/users.db`` with dev-bypass rows and ``data/biomarker_tracking.db``
    with test patients/measurements.
    """
    from engine.tracking import db as _tdb
    from engine.users import db as _udb

    monkeypatch.setattr(_udb, "_DEFAULT_PATH", tmp_path / "users.db")
    # Force the SQLite branch regardless of any DATABASE_URL in the dev
    # shell environment — mirrors test_api.py's existing client fixture.
    monkeypatch.setattr(_udb, "_is_postgres_configured", lambda path: False)
    _udb.reset_initialized()
    monkeypatch.setattr(_tdb, "_DEFAULT_PATH", tmp_path / "tracking.db")
    monkeypatch.setattr(_tdb, "_is_postgres_configured", lambda path: False)
    _tdb.reset_initialized()
    yield
    _udb.reset_initialized()
    _tdb.reset_initialized()
