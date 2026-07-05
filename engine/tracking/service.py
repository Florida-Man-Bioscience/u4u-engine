"""
engine/tracking/service.py
=========================
CRUD operations for patients, treatments, and measurements.

Identifiers are random hex strings (16 chars) — short enough for URLs,
long enough that collisions are negligible at the scale this is meant for.

SQL uses %s placeholders (psycopg2 / Postgres). Row results are normalised
via _row() so the same code handles both RealDictCursor (Postgres) and
sqlite3.Row (SQLite fallback in tests).
"""
from __future__ import annotations

import csv
import io
import json
import secrets
from collections.abc import Iterable
from datetime import datetime

from .models import Measurement, Patient, Treatment


def _new_id() -> str:
    return secrets.token_hex(8)


def _row(row) -> dict:
    """Normalise a psycopg2 RealDictRow or sqlite3.Row to a plain dict,
    converting any datetime values to ISO-8601 strings."""
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, datetime):
            d[k] = v.isoformat()
    return d


def _ph(conn) -> str:
    """Return the right parameter placeholder (%s for Postgres, ? for SQLite)."""
    return "%s" if getattr(conn, "_is_pg", False) else "?"


# ── Patients ────────────────────────────────────────────────────────────────

def create_patient(
    conn,
    *,
    label: str,
    sex: str | None = None,
    birth_year: int | None = None,
    notes: str | None = None,
    created_by_user_id: str | None = None,
) -> Patient:
    ph = _ph(conn)
    pid = _new_id()
    conn.execute(
        f"INSERT INTO patients (id, label, sex, birth_year, notes, created_by_user_id) "
        f"VALUES ({ph},{ph},{ph},{ph},{ph},{ph})",
        (pid, label, sex, birth_year, notes, created_by_user_id),
    )
    conn.commit()
    return get_patient(conn, pid)  # type: ignore[return-value]


def get_patient(conn, patient_id: str) -> Patient | None:
    ph = _ph(conn)
    row = conn.execute(f"SELECT * FROM patients WHERE id = {ph}", (patient_id,)).fetchone()
    return Patient(**_row(row)) if row else None


def list_patients(conn) -> list[Patient]:
    rows = conn.execute("SELECT * FROM patients ORDER BY created_at DESC").fetchall()
    return [Patient(**_row(r)) for r in rows]


def delete_patient(conn, patient_id: str) -> bool:
    ph = _ph(conn)
    cur = conn.execute(f"DELETE FROM patients WHERE id = {ph}", (patient_id,))
    conn.commit()
    return cur.rowcount > 0


# ── Treatments ──────────────────────────────────────────────────────────────

def create_treatment(
    conn,
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
    created_by_user_id: str | None = None,
) -> Treatment:
    ph = _ph(conn)
    tid = _new_id()
    conn.execute(
        f"""INSERT INTO treatments
           (id, patient_id, peptide_name, dose, dose_unit, schedule, route,
            start_date, end_date, notes, created_by_user_id)
           VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})""",
        (tid, patient_id, peptide_name, dose, dose_unit, schedule, route,
         start_date, end_date, notes, created_by_user_id),
    )
    conn.commit()
    return get_treatment(conn, tid)  # type: ignore[return-value]


def get_treatment(conn, treatment_id: str) -> Treatment | None:
    ph = _ph(conn)
    row = conn.execute(f"SELECT * FROM treatments WHERE id = {ph}", (treatment_id,)).fetchone()
    return Treatment(**_row(row)) if row else None


def list_treatments_for_patient(conn, patient_id: str) -> list[Treatment]:
    ph = _ph(conn)
    rows = conn.execute(
        f"SELECT * FROM treatments WHERE patient_id = {ph} ORDER BY start_date DESC",
        (patient_id,),
    ).fetchall()
    return [Treatment(**_row(r)) for r in rows]


def list_treatments_by_peptide(conn, peptide_name: str) -> list[Treatment]:
    ph = _ph(conn)
    rows = conn.execute(
        f"SELECT * FROM treatments WHERE peptide_name = {ph} ORDER BY start_date",
        (peptide_name,),
    ).fetchall()
    return [Treatment(**_row(r)) for r in rows]


# ── Measurements ────────────────────────────────────────────────────────────

def create_measurement(
    conn,
    *,
    patient_id: str,
    biomarker_name: str,
    value: float,
    measured_at: str,
    treatment_id: str | None = None,
    modality: str | None = None,
    unit: str | None = None,
    notes: str | None = None,
    created_by_user_id: str | None = None,
) -> Measurement:
    ph = _ph(conn)
    mid = _new_id()
    conn.execute(
        f"""INSERT INTO measurements
           (id, patient_id, treatment_id, biomarker_name, modality,
            value, unit, measured_at, notes, created_by_user_id)
           VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})""",
        (mid, patient_id, treatment_id, biomarker_name, modality,
         value, unit, measured_at, notes, created_by_user_id),
    )
    conn.commit()
    return get_measurement(conn, mid)  # type: ignore[return-value]


def get_measurement(conn, measurement_id: str) -> Measurement | None:
    ph = _ph(conn)
    row = conn.execute(
        f"SELECT * FROM measurements WHERE id = {ph}", (measurement_id,)
    ).fetchone()
    return Measurement(**_row(row)) if row else None


def list_measurements_for_patient(
    conn,
    patient_id: str,
    *,
    biomarker_name: str | None = None,
) -> list[Measurement]:
    ph = _ph(conn)
    if biomarker_name:
        rows = conn.execute(
            f"""SELECT * FROM measurements
               WHERE patient_id = {ph} AND biomarker_name = {ph}
               ORDER BY measured_at""",
            (patient_id, biomarker_name),
        ).fetchall()
    else:
        rows = conn.execute(
            f"SELECT * FROM measurements WHERE patient_id = {ph} ORDER BY measured_at",
            (patient_id,),
        ).fetchall()
    return [Measurement(**_row(r)) for r in rows]


def bulk_create_measurements(
    conn,
    records: Iterable[dict],
    *,
    created_by_user_id: str | None = None,
) -> list[Measurement]:
    """Insert many measurements in one transaction. Each record needs
    patient_id, biomarker_name, value, measured_at. Other fields optional."""
    ph = _ph(conn)
    out: list[Measurement] = []
    cur = conn.cursor()
    for r in records:
        mid = _new_id()
        cur.execute(
            f"""INSERT INTO measurements
               (id, patient_id, treatment_id, biomarker_name, modality,
                value, unit, measured_at, notes, created_by_user_id)
               VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})""",
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
                created_by_user_id,
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
            created_by_user_id=created_by_user_id,
        ))
    conn.commit()
    return out


# ── CSV import ──────────────────────────────────────────────────────────────

CSV_REQUIRED = {"patient_id", "biomarker_name", "value", "measured_at"}
CSV_OPTIONAL = {"treatment_id", "modality", "unit", "notes"}


# ── Genetic profile ─────────────────────────────────────────────────────────

def set_genetic_profile(
    conn,
    patient_id: str,
    profile_json: str,
    *,
    source: str = "synthetic",
) -> None:
    """Upsert a genetic profile for a patient."""
    ph = _ph(conn)
    now_fn = "NOW()" if ph == "%s" else "strftime('%Y-%m-%dT%H:%M:%fZ','now')"
    conn.execute(
        f"""INSERT INTO patient_genetics (patient_id, profile_json, source)
           VALUES ({ph}, {ph}, {ph})
           ON CONFLICT(patient_id) DO UPDATE SET
               profile_json = EXCLUDED.profile_json,
               source = EXCLUDED.source,
               created_at = {now_fn}""",
        (patient_id, profile_json, source),
    )
    conn.commit()


def get_genetic_profile_json(
    conn, patient_id: str
) -> tuple[str, str, str] | None:
    """Return (profile_json, source, created_at) or None."""
    ph = _ph(conn)
    row = conn.execute(
        f"SELECT profile_json, source, created_at FROM patient_genetics WHERE patient_id = {ph}",
        (patient_id,),
    ).fetchone()
    if row is None:
        return None
    d = _row(row)
    return d["profile_json"], d["source"], d["created_at"]


def set_patient_enrichment(conn, patient_id: str, enrichment_json: str) -> None:
    """Upsert per-patient pipeline enrichment (PRS profile, BPC-157 composite).

    ``enrichment_json`` is a JSON object string keyed by the channel the responder
    feature adapters read (``prs_profile``, ``bpc157``). Written at
    ``POST /tracking/patients/from-job``.
    """
    ph = _ph(conn)
    now_fn = "NOW()" if ph == "%s" else "strftime('%Y-%m-%dT%H:%M:%fZ','now')"
    conn.execute(
        f"""INSERT INTO patient_enrichment (patient_id, enrichment_json)
           VALUES ({ph}, {ph})
           ON CONFLICT(patient_id) DO UPDATE SET
               enrichment_json = EXCLUDED.enrichment_json,
               created_at = {now_fn}""",
        (patient_id, enrichment_json),
    )
    conn.commit()


def get_patient_enrichment(conn, patient_id: str) -> dict | None:
    """Return the patient's stored pipeline-enrichment dict, or None.

    Malformed/non-object JSON returns None so a corrupt row degrades to the
    graceful adapter no-op rather than raising into predict_response.
    """
    ph = _ph(conn)
    row = conn.execute(
        f"SELECT enrichment_json FROM patient_enrichment WHERE patient_id = {ph}",
        (patient_id,),
    ).fetchone()
    if row is None:
        return None
    try:
        parsed = json.loads(_row(row)["enrichment_json"])
    except (ValueError, TypeError):
        return None
    return parsed if isinstance(parsed, dict) else None


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
