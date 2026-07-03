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
