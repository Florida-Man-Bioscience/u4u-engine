"""
Tests for HealthKit ingestion (engine/healthkit).

Runs against the SQLite fallback (explicit temp path forces SQLite regardless of
DATABASE_URL), so no Postgres is required.
"""
from __future__ import annotations

from datetime import UTC, datetime, timezone
from uuid import uuid4

from engine.healthkit import service
from engine.healthkit.db import get_conn, reset_initialized
from engine.healthkit.schemas import SampleIn, SourceIn, WorkoutIn


def _sample(cls="quantity", type_id="HKQuantityTypeIdentifierStepCount", value=100.0, unit="count", workout=None):
    now = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
    return SampleIn(
        uuid=uuid4(),
        cls=cls,
        type=type_id,
        value=value,
        unit=unit,
        start=now,
        end=now,
        source=SourceIn(name="Apple Watch", bundleId="com.apple.health"),
        device={"name": "Watch", "model": "Watch7,1"},
        metadata={"foo": "bar"},
        workout=workout,
    )


def test_ingest_counts_received_and_inserted(tmp_path):
    reset_initialized()
    db = str(tmp_path / "hk.db")
    samples = [_sample(), _sample()]
    with get_conn(path=db) as conn:
        received, inserted = service.ingest(conn, subject_id="S-1", samples=samples)
    assert (received, inserted) == (2, 2)


def test_reingest_same_uuid_is_idempotent(tmp_path):
    reset_initialized()
    db = str(tmp_path / "hk.db")
    samples = [_sample()]
    with get_conn(path=db) as conn:
        service.ingest(conn, subject_id="S-1", samples=samples)
    with get_conn(path=db) as conn:
        received, inserted = service.ingest(conn, subject_id="S-1", samples=samples)
    assert received == 1
    assert inserted == 0  # ON CONFLICT DO NOTHING


def test_read_back_samples(tmp_path):
    reset_initialized()
    db = str(tmp_path / "hk.db")
    with get_conn(path=db) as conn:
        service.ingest(conn, subject_id="S-9", samples=[_sample(value=72.0, type_id="HKQuantityTypeIdentifierHeartRate", unit="count/min")])
    with get_conn(path=db) as conn:
        rows = service.read_samples(conn, subject_id="S-9")
    assert len(rows) == 1
    assert rows[0]["type_identifier"] == "HKQuantityTypeIdentifierHeartRate"
    assert rows[0]["value"] == 72.0
    assert rows[0]["metadata"] == {"foo": "bar"}   # JSON decoded


def test_workout_row_created(tmp_path):
    reset_initialized()
    db = str(tmp_path / "hk.db")
    workout = WorkoutIn(activityType="running", durationSeconds=1800.0, totalEnergyKcal=250.0, totalDistanceMeters=5000.0)
    sample = _sample(cls="workout", type_id="HKWorkoutTypeIdentifier", value=None, unit=None, workout=workout)
    with get_conn(path=db) as conn:
        service.ingest(conn, subject_id="S-2", samples=[sample])
        row = conn.execute("SELECT * FROM healthkit_workouts").fetchone()
    assert row is not None
    assert dict(row)["activity_type"] == "running"


def test_audit_row_written(tmp_path):
    reset_initialized()
    db = str(tmp_path / "hk.db")
    with get_conn(path=db) as conn:
        service.ingest(conn, subject_id="S-3", samples=[_sample(), _sample()], source_name="Apple Watch")
        audit = conn.execute("SELECT * FROM healthkit_ingestions WHERE subject_id = 'S-3'").fetchone()
    assert dict(audit)["sample_count"] == 2
    assert dict(audit)["inserted_count"] == 2


# ── Device-token auth ─────────────────────────────────────────────────────────

def _mint(db, raw, *, label=None, subject_id=None):
    with get_conn(path=db) as conn:
        from engine.healthkit.auth import hash_token
        conn.execute(
            "INSERT INTO healthkit_device_tokens (token_hash, label, subject_id) VALUES (?,?,?)",
            (hash_token(raw), label, subject_id),
        )
        conn.commit()


def test_token_required_fail_closed_in_prod(monkeypatch):
    from engine.healthkit import auth
    monkeypatch.delenv("HEALTHKIT_REQUIRE_TOKEN", raising=False)
    monkeypatch.setattr("db.pool.DATABASE_URL", "", raising=False)
    assert auth.token_required() is False            # no DB, no flag → open (dev)
    monkeypatch.setenv("HEALTHKIT_REQUIRE_TOKEN", "1")
    assert auth.token_required() is True             # dev can be forced closed
    monkeypatch.delenv("HEALTHKIT_REQUIRE_TOKEN", raising=False)
    monkeypatch.setattr("db.pool.DATABASE_URL", "postgresql://x", raising=False)
    assert auth.token_required() is True             # DB set → always required (prod)
    # No env var can open a Postgres-backed deployment (fail-closed footgun fixed).
    monkeypatch.setenv("HEALTHKIT_ALLOW_ANONYMOUS", "1")
    assert auth.token_required() is True


def test_require_device_token(tmp_path, monkeypatch):
    reset_initialized()
    db = str(tmp_path / "hk.db")
    import pytest
    from fastapi import HTTPException
    from fastapi.security import HTTPAuthorizationCredentials

    from engine.healthkit import auth

    # Route the dependency's connection at our temp SQLite DB.
    monkeypatch.setattr(auth, "get_conn", lambda: get_conn(path=db))
    monkeypatch.setenv("HEALTHKIT_REQUIRE_TOKEN", "1")

    raw = "pep_hk_valid"
    _mint(db, raw, label="iPhone")

    def creds(tok):
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials=tok)

    assert auth.require_device_token(creds(raw))["label"] == "iPhone"          # valid
    with pytest.raises(HTTPException) as e1:
        auth.require_device_token(creds("nope"))                               # invalid → 401
    assert e1.value.status_code == 401
    with pytest.raises(HTTPException) as e2:
        auth.require_device_token(None)                                        # missing+required → 401
    assert e2.value.status_code == 401


def test_require_device_token_anon_when_open(tmp_path, monkeypatch):
    from engine.healthkit import auth
    monkeypatch.setattr(auth, "get_conn", lambda: get_conn(path=str(tmp_path / "hk.db")))
    monkeypatch.delenv("HEALTHKIT_REQUIRE_TOKEN", raising=False)
    monkeypatch.setattr("db.pool.DATABASE_URL", "", raising=False)
    assert auth.require_device_token(None) is None    # no DB, no flag → anonymous allowed


def test_enforce_subject_binding():
    import pytest
    from fastapi import HTTPException

    from engine.healthkit.auth import enforce_subject
    enforce_subject(None, "S-1")                           # no token → ok (dev)
    enforce_subject({"subject_id": None}, "S-1")           # unbound token → ok for writes
    enforce_subject({"subject_id": "S-1"}, "S-1")          # bound match → ok
    with pytest.raises(HTTPException) as e:
        enforce_subject({"subject_id": "S-2"}, "S-1")      # bound mismatch → 403
    assert e.value.status_code == 403
    # Empty-string binding must NOT be treated as unbound (was a silent bypass).
    with pytest.raises(HTTPException) as e_empty:
        enforce_subject({"subject_id": ""}, "S-1")
    assert e_empty.value.status_code == 403


def test_enforce_subject_read_requires_bound_token():
    import pytest
    from fastapi import HTTPException

    from engine.healthkit.auth import enforce_subject
    enforce_subject(None, "S-1", require_bound=True)              # dev open → ok
    enforce_subject({"subject_id": "S-1"}, "S-1", require_bound=True)  # bound match → ok
    with pytest.raises(HTTPException) as e:                       # unbound token → 403 on read
        enforce_subject({"subject_id": None}, "S-1", require_bound=True)
    assert e.value.status_code == 403


# ── Enrollment (self-service onboarding) ──────────────────────────────────────

def test_mint_and_bind_device_token(tmp_path):
    reset_initialized()
    db = str(tmp_path / "hk.db")
    with get_conn(path=db) as conn:
        assert service.subject_has_active_token(conn, "S-enroll") is False
        raw = service.mint_device_token(conn, subject_id="S-enroll", label="enrolled")
        assert raw.startswith("pep_hk_")
        assert service.subject_has_active_token(conn, "S-enroll") is True


def test_minted_token_authorizes_that_subject(tmp_path):
    from engine.healthkit.auth import enforce_subject, hash_token
    reset_initialized()
    db = str(tmp_path / "hk.db")
    with get_conn(path=db) as conn:
        raw = service.mint_device_token(conn, subject_id="S-bound", label="enrolled")
        ph = "%s" if getattr(conn, "_is_pg", False) else "?"
        row = dict(conn.execute(
            f"SELECT * FROM healthkit_device_tokens WHERE token_hash = {ph}",
            (hash_token(raw),),
        ).fetchone())
    # Bound token may touch its subject, not another.
    enforce_subject(row, "S-bound")  # no raise
    try:
        enforce_subject(row, "S-other")
        raised = False
    except Exception:
        raised = True
    assert raised


def test_enrollment_code_validation(monkeypatch):
    from engine.healthkit import auth
    monkeypatch.delenv("HEALTHKIT_ENROLL_CODES", raising=False)
    assert auth.enrollment_enabled() is False
    assert auth.is_valid_enrollment_code("anything") is False

    monkeypatch.setenv("HEALTHKIT_ENROLL_CODES", "alpha, bravo")
    assert auth.enrollment_enabled() is True
    assert auth.is_valid_enrollment_code("alpha") is True
    assert auth.is_valid_enrollment_code("bravo") is True
    assert auth.is_valid_enrollment_code("charlie") is False
