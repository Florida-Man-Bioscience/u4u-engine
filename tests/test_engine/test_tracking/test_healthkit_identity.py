"""
Round-trip tests for the HealthKit ↔ tracking identity bridge.

The map table lives in the HealthKit database (engine/healthkit/schema.sql),
so these use a HealthKit SQLite connection. SQLite is the CI backend.
"""
from __future__ import annotations

import pytest

from engine.healthkit import db as hk_db
from engine.healthkit.db import get_conn
from engine.tracking.healthkit_identity import (
    link_subject_to_patient,
    resolve_patient_id,
    resolve_subject_id,
)


@pytest.fixture
def conn():
    hk_db.reset_initialized()
    with get_conn(":memory:") as c:
        yield c


def test_link_and_resolve_roundtrip(conn):
    link_subject_to_patient(conn, "subj-abc", "P-001")
    assert resolve_patient_id(conn, "subj-abc") == "P-001"
    assert resolve_subject_id(conn, "P-001") == "subj-abc"


def test_resolve_unknown_returns_none(conn):
    assert resolve_patient_id(conn, "nope") is None
    assert resolve_subject_id(conn, "nope") is None


def test_relink_is_idempotent_upsert(conn):
    link_subject_to_patient(conn, "subj-x", "P-001")
    # Re-point the same subject at a different patient — upsert, not error.
    link_subject_to_patient(conn, "subj-x", "P-002")
    assert resolve_patient_id(conn, "subj-x") == "P-002"
    # Only one row for the subject.
    rows = conn.execute(
        "SELECT COUNT(*) AS n FROM healthkit_subject_map WHERE subject_id = ?",
        ("subj-x",),
    ).fetchone()
    assert rows["n"] == 1


def test_multiple_subjects_one_patient(conn):
    link_subject_to_patient(conn, "subj-1", "P-100")
    link_subject_to_patient(conn, "subj-2", "P-100")
    assert resolve_patient_id(conn, "subj-1") == "P-100"
    assert resolve_patient_id(conn, "subj-2") == "P-100"
    # Inverse resolves deterministically to the earliest/lowest subject.
    assert resolve_subject_id(conn, "P-100") == "subj-1"
