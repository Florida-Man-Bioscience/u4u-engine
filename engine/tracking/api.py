"""
engine/tracking/api.py
======================
FastAPI router for the biomarker tracking subsystem.

Mount in api.py via:
    from engine.tracking.api import router as tracking_router
    app.include_router(tracking_router)
"""
from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from engine.peptides import PEPTIDE_BIOMARKERS, get_biomarker_panel

from . import analysis, service
from .db import get_conn
from .genetics import (
    GeneticProfile,
    derive_responder_prior,
    generate_synthetic_profile,
)
from .pharmgkb_catalog import PEPTIDES_WITH_EVIDENCE
from .profile_from_job import build_profile_from_job_results, evidence_payload


router = APIRouter(prefix="/tracking", tags=["tracking"])


# ── Connection dependency ───────────────────────────────────────────────────
# A single shared connection is fine here: SQLite + WAL mode handles
# concurrent reads, and check_same_thread=False lets FastAPI's worker
# threads share it. Override via _override_conn for tests.

_override_conn: sqlite3.Connection | None = None


def _conn() -> sqlite3.Connection:
    if _override_conn is not None:
        return _override_conn
    return get_conn()


def set_test_conn(conn: sqlite3.Connection | None) -> None:
    """Test helper — inject a connection (typically :memory:)."""
    global _override_conn
    _override_conn = conn


# ── Request bodies ──────────────────────────────────────────────────────────

class PatientIn(BaseModel):
    label: str = Field(min_length=1, max_length=64)
    sex: str | None = Field(default=None, max_length=16)
    birth_year: int | None = Field(default=None, ge=1900, le=2100)
    notes: str | None = None


class TreatmentIn(BaseModel):
    peptide_name: str = Field(min_length=1, max_length=64)
    start_date: str = Field(min_length=10, max_length=10)  # YYYY-MM-DD
    end_date: str | None = None
    dose: float | None = None
    dose_unit: str | None = None
    schedule: str | None = None
    route: str | None = None
    notes: str | None = None


class MeasurementIn(BaseModel):
    patient_id: str
    biomarker_name: str = Field(min_length=1, max_length=128)
    value: float
    measured_at: str = Field(min_length=10)  # ISO date or datetime
    treatment_id: str | None = None
    modality: str | None = None
    unit: str | None = None
    notes: str | None = None


class BulkMeasurementsIn(BaseModel):
    measurements: list[MeasurementIn]


class PatientFromJobIn(BaseModel):
    """Optional payload for ``POST /tracking/patients/from-job/{job_id}``.

    Everything is optional: if the caller doesn't specify a label, we
    derive one from the source filename so the auto-created patient is
    still recognisable in the patient list.
    """
    label: str | None = Field(default=None, max_length=64)
    sex: str | None = Field(default=None, max_length=16)
    birth_year: int | None = Field(default=None, ge=1900, le=2100)
    notes: str | None = None


# ── Patients ────────────────────────────────────────────────────────────────

@router.post("/patients")
def create_patient(body: PatientIn) -> dict[str, Any]:
    p = service.create_patient(
        _conn(),
        label=body.label,
        sex=body.sex,
        birth_year=body.birth_year,
        notes=body.notes,
    )
    return p.to_dict()


@router.get("/patients")
def list_patients() -> list[dict[str, Any]]:
    return [p.to_dict() for p in service.list_patients(_conn())]


@router.get("/patients/{patient_id}")
def get_patient(patient_id: str) -> dict[str, Any]:
    p = service.get_patient(_conn(), patient_id)
    if p is None:
        raise HTTPException(404, "patient not found")
    return p.to_dict()


@router.delete("/patients/{patient_id}")
def delete_patient(patient_id: str) -> dict[str, Any]:
    ok = service.delete_patient(_conn(), patient_id)
    if not ok:
        raise HTTPException(404, "patient not found")
    return {"deleted": True}


# ── Treatments ──────────────────────────────────────────────────────────────

@router.post("/patients/{patient_id}/treatments")
def create_treatment(patient_id: str, body: TreatmentIn) -> dict[str, Any]:
    if service.get_patient(_conn(), patient_id) is None:
        raise HTTPException(404, "patient not found")
    if body.peptide_name not in PEPTIDE_BIOMARKERS and get_biomarker_panel(body.peptide_name) is None:
        # Allow free-text peptides but warn — useful for combos / aliases.
        # We don't reject so users can track therapies the panel doesn't cover.
        pass
    t = service.create_treatment(
        _conn(),
        patient_id=patient_id,
        peptide_name=body.peptide_name,
        start_date=body.start_date,
        dose=body.dose,
        dose_unit=body.dose_unit,
        schedule=body.schedule,
        route=body.route,
        end_date=body.end_date,
        notes=body.notes,
    )
    return t.to_dict()


@router.get("/patients/{patient_id}/treatments")
def list_treatments(patient_id: str) -> list[dict[str, Any]]:
    return [t.to_dict() for t in service.list_treatments_for_patient(_conn(), patient_id)]


# ── Measurements ────────────────────────────────────────────────────────────

@router.post("/measurements")
def create_measurement(body: MeasurementIn) -> dict[str, Any]:
    if service.get_patient(_conn(), body.patient_id) is None:
        raise HTTPException(404, "patient not found")
    m = service.create_measurement(
        _conn(),
        patient_id=body.patient_id,
        biomarker_name=body.biomarker_name,
        value=body.value,
        measured_at=body.measured_at,
        treatment_id=body.treatment_id,
        modality=body.modality,
        unit=body.unit,
        notes=body.notes,
    )
    return m.to_dict()


@router.post("/measurements/bulk")
def bulk_measurements(body: BulkMeasurementsIn) -> dict[str, Any]:
    if not body.measurements:
        raise HTTPException(400, "no measurements provided")
    records = [m.model_dump() for m in body.measurements]
    created = service.bulk_create_measurements(_conn(), records)
    return {"created": len(created), "ids": [m.id for m in created]}


@router.post("/measurements/csv")
async def upload_csv(file: UploadFile = File(...)) -> dict[str, Any]:
    raw = await file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(400, "file is not UTF-8")
    records, errors = service.parse_measurement_csv(text)
    if not records:
        raise HTTPException(400, {"errors": errors})
    created = service.bulk_create_measurements(_conn(), records)
    return {"created": len(created), "errors": errors}


@router.get("/patients/{patient_id}/measurements")
def list_measurements(patient_id: str, biomarker: str | None = None) -> list[dict[str, Any]]:
    rows = service.list_measurements_for_patient(
        _conn(), patient_id, biomarker_name=biomarker
    )
    return [m.to_dict() for m in rows]


# ── Analysis / catalog ──────────────────────────────────────────────────────

@router.get("/peptides")
def peptides_with_data() -> list[dict[str, Any]]:
    return analysis.peptides_with_data(_conn())


@router.get("/peptides/{peptide_name}/biomarkers")
def peptide_biomarker_catalog(peptide_name: str) -> list[dict[str, Any]]:
    return analysis.available_biomarkers(_conn(), peptide_name)


@router.get("/cohort")
def cohort(
    peptide: str,
    biomarker: str,
    dose_min: float | None = None,
    dose_max: float | None = None,
) -> dict[str, Any]:
    result = analysis.cohort_trajectories(
        _conn(),
        peptide_name=peptide,
        biomarker_name=biomarker,
        dose_min=dose_min,
        dose_max=dose_max,
    )
    return result.to_dict()


# ── Genetic profile + Bayesian predictions ──────────────────────────────────

@router.get("/patients/{patient_id}/genetics")
def get_genetics(patient_id: str) -> dict[str, Any]:
    if service.get_patient(_conn(), patient_id) is None:
        raise HTTPException(404, "patient not found")
    raw = service.get_genetic_profile_json(_conn(), patient_id)
    if raw is None:
        return {"profile": None, "source": None, "created_at": None}
    profile_json, source, created_at = raw
    profile = GeneticProfile.from_json(profile_json)
    return {
        "profile": profile.to_dict(),
        "source": source,
        "created_at": created_at,
    }


@router.post("/patients/{patient_id}/genetics/synthetic")
def generate_genetics(patient_id: str, seed: int | None = None) -> dict[str, Any]:
    """Generate (or regenerate) a synthetic genetic profile for a patient."""
    if service.get_patient(_conn(), patient_id) is None:
        raise HTTPException(404, "patient not found")
    import random
    rng = random.Random(seed) if seed is not None else random.Random()
    profile = generate_synthetic_profile(rng)
    service.set_genetic_profile(
        _conn(), patient_id, profile.to_json(), source="synthetic"
    )
    return {
        "profile": profile.to_dict(),
        "source": "synthetic",
    }


@router.post("/patients/from-job/{job_id}")
def create_patient_from_job(
    job_id: str, body: PatientFromJobIn | None = None
) -> dict[str, Any]:
    """Create a tracking patient pre-populated from a completed /analyze job.

    Single round-trip from the results page: caller passes the job_id;
    we (1) fetch the job's annotated variants, (2) build a real-data
    ``GeneticProfile`` against the evidence-based PharmGKB catalog,
    (3) create a ``Patient`` row, and (4) attach the profile. The
    response carries everything the UI needs to navigate to the new
    patient page and render its genetic context.

    Errors:
      404 — job not found, or job not yet complete.
    """
    # Lazy import to keep this router free of a top-level dependency on
    # the root api.py (which would otherwise be circular).
    from api import get_completed_job_results, get_job_filename

    job_results = get_completed_job_results(job_id)
    if job_results is None:
        raise HTTPException(404, "job not found or not complete")

    # Default the patient label to something readable when the caller
    # didn't supply one — "Patient from <filename>" beats a bare UUID
    # in the patient list.
    payload = body or PatientFromJobIn()
    if payload.label:
        label = payload.label
    else:
        fname = get_job_filename(job_id) or job_id[:8]
        label = f"Patient from {fname}"[:64]

    patient = service.create_patient(
        _conn(),
        label=label,
        sex=payload.sex,
        birth_year=payload.birth_year,
        notes=payload.notes,
    )
    profile = build_profile_from_job_results(job_results, job_id=job_id)
    service.set_genetic_profile(
        _conn(), patient.id, profile.to_json(), source=f"job:{job_id}"
    )

    # Surface coverage stats so the UI can render an honest "we found
    # priors for K of N peptides" line on the results page.
    covered_with_signal = sorted(
        {
            pep
            for v in profile.variants
            if v.dosage > 0
            for pep in v.peptide_effects
            if v.peptide_effects[pep] != 0.0
        }
    )
    evidence = [
        {
            "rsid": v.rsid,
            "gene": v.gene,
            "genotype": v.genotype,
            "dosage": v.dosage,
            "evidence": evidence_payload(v.rsid),
        }
        for v in profile.variants
        if v.dosage > 0
    ]

    # Top engine peptide recommendations — used by the onboarding flow
    # to suggest which peptide(s) the patient should consider trialling
    # first. We do NOT use these to shift the Bayesian prior (the user
    # picked "PharmGKB-only" for that); they're a navigation aid only.
    raw_recs = (
        (job_results.get("peptide_recommendations") or {}).get("recommendations")
        or []
    )
    _TIER_ORDER = {
        "Strong Fit": 0,
        "Possible Fit": 1,
        "Baseline": 2,
        "Possibly Altered": 3,
        "Review Recommended": 4,
        "Review Needed": 4,
        "Likely Reduced": 5,
        "Altered / Reduced": 5,
        "Caution": 6,
    }
    engine_recs = sorted(
        (
            {
                "peptide_name": rec.get("peptide_name"),
                "category": rec.get("category"),
                "predicted_tier": rec.get("predicted_tier"),
                "prediction_description": rec.get("prediction_description"),
                "has_pharmgkb_evidence": rec.get("peptide_name") in PEPTIDES_WITH_EVIDENCE,
                "has_patient_signal": rec.get("peptide_name") in covered_with_signal,
            }
            for rec in raw_recs
            if rec.get("peptide_name")
        ),
        key=lambda r: (
            _TIER_ORDER.get(r["predicted_tier"] or "", 7),
            0 if r["has_patient_signal"] else 1,
            r["peptide_name"] or "",
        ),
    )

    return {
        "patient": patient.to_dict(),
        "profile": profile.to_dict(),
        "source": f"job:{job_id}",
        "peptides_with_evidence": sorted(PEPTIDES_WITH_EVIDENCE),
        "peptides_with_patient_signal": covered_with_signal,
        "variants_carried": evidence,
        "engine_recommendations": engine_recs,
    }


@router.get("/patients/{patient_id}/predictions")
def get_predictions(
    patient_id: str, peptide: str, biomarker: str
) -> dict[str, Any]:
    """Bayesian prediction for one (patient, peptide, biomarker)."""
    if service.get_patient(_conn(), patient_id) is None:
        raise HTTPException(404, "patient not found")
    return analysis.predict_response(
        _conn(),
        patient_id=patient_id,
        peptide_name=peptide,
        biomarker_name=biomarker,
    )


@router.get("/patients/{patient_id}/priors")
def get_priors(patient_id: str) -> dict[str, Any]:
    """All per-peptide responder-strength priors derived from the patient's
    genetic profile. r=1.0 is an average responder; r>1 stronger, r<1 weaker.

    Per-biomarker % change priors require a biomarker context and are
    surfaced by /tracking/patients/{id}/predictions.
    """
    if service.get_patient(_conn(), patient_id) is None:
        raise HTTPException(404, "patient not found")
    raw = service.get_genetic_profile_json(_conn(), patient_id)
    if raw is None:
        return {"priors": []}
    profile = GeneticProfile.from_json(raw[0])
    priors: list[dict[str, Any]] = []
    for peptide_name in sorted(PEPTIDE_BIOMARKERS.keys()):
        r = derive_responder_prior(profile, peptide_name)
        priors.append(r.to_dict())
    return {"priors": priors}


# ── Demo data seed ──────────────────────────────────────────────────────────

class SeedIn(BaseModel):
    force: bool = False
    patients: int = Field(default=12, ge=1, le=100)
    seed: int = 42


@router.post("/seed")
def seed_demo_data(body: SeedIn | None = None) -> dict[str, Any]:
    """Populate the tracking DB with synthetic demo data.

    Idempotent by default: returns ``{"skipped": N}`` if patients already
    exist. Pass ``{"force": true}`` to wipe (FK cascade) and reseed.
    """
    import random

    from .seed import seed as run_seed

    body = body or SeedIn()
    stats = run_seed(
        _conn(),
        rng=random.Random(body.seed),
        n_patients=body.patients,
        force=body.force,
    )
    return stats
