"""
engine/tracking/service.py
=========================
CRUD operations for patients, treatments, and measurements.

Identifiers are random hex strings (16 chars) — short enough for URLs,
long enough that collisions are negligible at the scale this is meant for.
"""
from __future__ import annotations

import csv
import io
import secrets
import sqlite3
from typing import Iterable

from .models import Measurement, Patient, Treatment


def _new_id() -> str:
    return secrets.token_hex(8)


# ── Patients ────────────────────────────────────────────────────────────────

def create_patient(
    conn: sqlite3.Connection,
    *,
    label: str,
    sex: str | None = None,
    birth_year: int | None = None,
    notes: str | None = None,
) -> Patient:
    pid = _new_id()
    conn.execute(
        "INSERT INTO patients (id, label, sex, birth_year, notes) VALUES (?,?,?,?,?)",
        (pid, label, sex, birth_year, notes),
    )
    conn.commit()
    return get_patient(conn, pid)  # type: ignore[return-value]


def get_patient(conn: sqlite3.Connection, patient_id: str) -> Patient | None:
    row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    return Patient(**dict(row)) if row else None


def list_patients(conn: sqlite3.Connection) -> list[Patient]:
    rows = conn.execute("SELECT * FROM patients ORDER BY created_at DESC").fetchall()
    return [Patient(**dict(r)) for r in rows]


def delete_patient(conn: sqlite3.Connection, patient_id: str) -> bool:
    cur = conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    conn.commit()
    return cur.rowcount > 0


# ── Treatments ──────────────────────────────────────────────────────────────

def create_treatment(
    conn: sqlite3.Connection,
    *,
    patient_id: str,
    peptide_name: str,
    start_date: str,
    dose: float | None = None,
    dose_unit: str | None = None,
    schedule: str | None = None,
    route: str | None = None,
    end_date: str | None = None,
    notes: str | None = None,
) -> Treatment:
    tid = _new_id()
    conn.execute(
        """INSERT INTO treatments
           (id, patient_id, peptide_name, dose, dose_unit, schedule, route,
            start_date, end_date, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (tid, patient_id, peptide_name, dose, dose_unit, schedule, route,
         start_date, end_date, notes),
    )
    conn.commit()
    return get_treatment(conn, tid)  # type: ignore[return-value]


def get_treatment(conn: sqlite3.Connection, treatment_id: str) -> Treatment | None:
    row = conn.execute("SELECT * FROM treatments WHERE id = ?", (treatment_id,)).fetchone()
    return Treatment(**dict(row)) if row else None


def list_treatments_for_patient(conn: sqlite3.Connection, patient_id: str) -> list[Treatment]:
    rows = conn.execute(
        "SELECT * FROM treatments WHERE patient_id = ? ORDER BY start_date DESC",
        (patient_id,),
    ).fetchall()
    return [Treatment(**dict(r)) for r in rows]


def list_treatments_by_peptide(conn: sqlite3.Connection, peptide_name: str) -> list[Treatment]:
    rows = conn.execute(
        "SELECT * FROM treatments WHERE peptide_name = ? ORDER BY start_date",
        (peptide_name,),
    ).fetchall()
    return [Treatment(**dict(r)) for r in rows]


# ── Measurements ────────────────────────────────────────────────────────────

def create_measurement(
    conn: sqlite3.Connection,
    *,
    patient_id: str,
    biomarker_name: str,
    value: float,
    measured_at: str,
    treatment_id: str | None = None,
    modality: str | None = None,
    unit: str | None = None,
    notes: str | None = None,
) -> Measurement:
    mid = _new_id()
    conn.execute(
        """INSERT INTO measurements
           (id, patient_id, treatment_id, biomarker_name, modality,
            value, unit, measured_at, notes)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (mid, patient_id, treatment_id, biomarker_name, modality,
         value, unit, measured_at, notes),
    )
    conn.commit()
    return get_measurement(conn, mid)  # type: ignore[return-value]


def get_measurement(conn: sqlite3.Connection, measurement_id: str) -> Measurement | None:
    row = conn.execute(
        "SELECT * FROM measurements WHERE id = ?", (measurement_id,)
    ).fetchone()
    return Measurement(**dict(row)) if row else None


def list_measurements_for_patient(
    conn: sqlite3.Connection,
    patient_id: str,
    *,
    biomarker_name: str | None = None,
) -> list[Measurement]:
    if biomarker_name:
        rows = conn.execute(
            """SELECT * FROM measurements
               WHERE patient_id = ? AND biomarker_name = ?
               ORDER BY measured_at""",
            (patient_id, biomarker_name),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM measurements WHERE patient_id = ? ORDER BY measured_at",
            (patient_id,),
        ).fetchall()
    return [Measurement(**dict(r)) for r in rows]


def bulk_create_measurements(
    conn: sqlite3.Connection,
    records: Iterable[dict],
) -> list[Measurement]:
    """Insert many measurements in one transaction. Each record needs
    patient_id, biomarker_name, value, measured_at. Other fields optional."""
    out: list[Measurement] = []
    cur = conn.cursor()
    for r in records:
        mid = _new_id()
        cur.execute(
            """INSERT INTO measurements
               (id, patient_id, treatment_id, biomarker_name, modality,
                value, unit, measured_at, notes)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                mid,
                r["patient_id"],
                r.get("treatment_id"),
                r["biomarker_name"],
                r.get("modality"),
                float(r["value"]),
                r.get("unit"),
                r["measured_at"],
                r.get("notes"),
            ),
        )
        out.append(Measurement(
            id=mid,
            patient_id=r["patient_id"],
            treatment_id=r.get("treatment_id"),
            biomarker_name=r["biomarker_name"],
            modality=r.get("modality"),
            value=float(r["value"]),
            unit=r.get("unit"),
            measured_at=r["measured_at"],
            notes=r.get("notes"),
            created_at="",
        ))
    conn.commit()
    return out


# ── CSV import ──────────────────────────────────────────────────────────────

CSV_REQUIRED = {"patient_id", "biomarker_name", "value", "measured_at"}
CSV_OPTIONAL = {"treatment_id", "modality", "unit", "notes"}


def parse_measurement_csv(text: str) -> tuple[list[dict], list[str]]:
    """Parse a CSV blob into measurement records.

    Returns (records, errors). Errors are per-row strings; records that
    failed validation are not included in the records list.
    """
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        return [], ["empty CSV"]
    missing = CSV_REQUIRED - set(reader.fieldnames)
    if missing:
        return [], [f"missing required columns: {', '.join(sorted(missing))}"]
    records: list[dict] = []
    errors: list[str] = []
    for i, row in enumerate(reader, start=2):  # header is row 1
        try:
            rec = {k: (row.get(k) or None) for k in CSV_OPTIONAL}
            rec["patient_id"] = row["patient_id"].strip()
            rec["biomarker_name"] = row["biomarker_name"].strip()
            rec["value"] = float(row["value"])
            rec["measured_at"] = row["measured_at"].strip()
            if not rec["patient_id"] or not rec["biomarker_name"] or not rec["measured_at"]:
                raise ValueError("required field empty")
            records.append(rec)
        except (KeyError, ValueError) as exc:
            errors.append(f"row {i}: {exc}")
    return records, errors
