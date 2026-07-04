"""
engine/tracking/healthkit_identity.py
======================================
Identity bridge between a de-identified HealthKit ``subject_id`` and a tracking
``patient_id``.

This is the seam that the unified peptide-effect model will use to pull
HealthKit-derived signals into a patient's prediction. Phase 0 ships only the
bridge: link + resolve both directions. No prediction wiring yet.

The map table (``healthkit_subject_map``) lives in the HealthKit database
(``engine/healthkit/schema.sql`` / ``db/migrations/010_healthkit_subject_map``),
so callers pass a HealthKit connection (``engine.healthkit.db.get_conn``). The
functions are placeholder-agnostic (Postgres ``%s`` vs SQLite ``?``) via the
same ``_is_pg`` sniff used across the tracking/healthkit services.
"""
from __future__ import annotations


def _ph(conn) -> str:
    """Return the right parameter placeholder (%s for Postgres, ? for SQLite)."""
    return "%s" if getattr(conn, "_is_pg", False) else "?"


def link_subject_to_patient(conn, subject_id: str, patient_id: str) -> None:
    """Create or update the ``subject_id → patient_id`` mapping (idempotent).

    Upserts on ``subject_id`` so re-linking a subject to a (possibly new)
    patient is a no-op-or-update rather than a duplicate-key error.
    """
    ph = _ph(conn)
    conn.execute(
        f"INSERT INTO healthkit_subject_map (subject_id, patient_id) "
        f"VALUES ({ph}, {ph}) "
        f"ON CONFLICT (subject_id) DO UPDATE SET patient_id = excluded.patient_id",
        (subject_id, patient_id),
    )
    conn.commit()


def resolve_patient_id(conn, subject_id: str) -> str | None:
    """Return the tracking ``patient_id`` linked to ``subject_id``, or None."""
    ph = _ph(conn)
    row = conn.execute(
        f"SELECT patient_id FROM healthkit_subject_map WHERE subject_id = {ph}",
        (subject_id,),
    ).fetchone()
    if row is None:
        return None
    return row["patient_id"]


def resolve_subject_id(conn, patient_id: str) -> str | None:
    """Inverse lookup: return the ``subject_id`` linked to ``patient_id``.

    If more than one subject maps to the same patient, the earliest-created is
    returned (deterministic).
    """
    ph = _ph(conn)
    row = conn.execute(
        f"SELECT subject_id FROM healthkit_subject_map "
        f"WHERE patient_id = {ph} ORDER BY created_at, subject_id LIMIT 1",
        (patient_id,),
    ).fetchone()
    if row is None:
        return None
    return row["subject_id"]
