"""
engine/tracking/api.py
======================
FastAPI router for the biomarker tracking subsystem.

Mount in api.py via:
    from engine.tracking.api import router as tracking_router
    app.include_router(tracking_router)
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from engine.peptides import PEPTIDE_BIOMARKERS, get_biomarker_panel
from engine.users.deps import current_user
from engine.users.models import User

from . import analysis, service
from .db import get_conn
from .genetics import (
    GeneticProfile,
    derive_responder_prior,
    generate_synthetic_profile,
)
from .pharmgkb_catalog import PEPTIDES_WITH_EVIDENCE
from .profile_from_job import build_profile_from_job_results, evidence_payload


def _user_id(user: User | None) -> str | None:
    """Tiny helper — the FastAPI dep yields a User or None; the service
    layer wants the bare id (or None in dev when no Authentik headers)."""
    return user.id if user is not None else None


router = APIRouter(prefix="/tracking", tags=["tracking"])


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
    """Optional payload for ``POST /tracking/patients/from-job/{job_id}``."""
    label: str | None = Field(default=None, max_length=64)
    sex: str | None = Field(default=None, max_length=16)
    birth_year: int | None = Field(default=None, ge=1900, le=2100)
    notes: str | None = None


# ── Patients ────────────────────────────────────────────────────────────────

@router.post("/patients")
def create_patient(
    body: PatientIn,
    user: User | None = Depends(current_user),
) -> dict[str, Any]:
    with get_conn() as conn:
        p = service.create_patient(
            conn,
            label=body.label,
            sex=body.sex,
            birth_year=body.birth_year,
            notes=body.notes,
            created_by_user_id=_user_id(user),
        )
    return p.to_dict()


@router.get("/patients")
def list_patients() -> list[dict[str, Any]]:
    with get_conn() as conn:
        return [p.to_dict() for p in service.list_patients(conn)]


@router.get("/patients/{patient_id}")
def get_patient(patient_id: str) -> dict[str, Any]:
    with get_conn() as conn:
        p = service.get_patient(conn, patient_id)
    if p is None:
        raise HTTPException(404, "patient not found")
    return p.to_dict()


@router.delete("/patients/{patient_id}")
def delete_patient(patient_id: str) -> dict[str, Any]:
    with get_conn() as conn:
        ok = service.delete_patient(conn, patient_id)
    if not ok:
        raise HTTPException(404, "patient not found")
    return {"deleted": True}


# ── Treatments ──────────────────────────────────────────────────────────────

@router.post("/patients/{patient_id}/treatments")
def create_treatment(
    patient_id: str,
    body: TreatmentIn,
    user: User | None = Depends(current_user),
) -> dict[str, Any]:
    with get_conn() as conn:
        if service.get_patient(conn, patient_id) is None:
            raise HTTPException(404, "patient not found")
        if body.peptide_name not in PEPTIDE_BIOMARKERS and get_biomarker_panel(body.peptide_name) is None:
            pass  # allow free-text peptides
        t = service.create_treatment(
            conn,
            patient_id=patient_id,
            peptide_name=body.peptide_name,
            start_date=body.start_date,
            dose=body.dose,
            dose_unit=body.dose_unit,
            schedule=body.schedule,
            route=body.route,
            end_date=body.end_date,
            notes=body.notes,
            created_by_user_id=_user_id(user),
        )
    return t.to_dict()


@router.get("/patients/{patient_id}/treatments")
def list_treatments(patient_id: str) -> list[dict[str, Any]]:
    with get_conn() as conn:
        return [t.to_dict() for t in service.list_treatments_for_patient(conn, patient_id)]


# ── Measurements ────────────────────────────────────────────────────────────

@router.post("/measurements")
def create_measurement(
    body: MeasurementIn,
    user: User | None = Depends(current_user),
) -> dict[str, Any]:
    with get_conn() as conn:
        if service.get_patient(conn, body.patient_id) is None:
            raise HTTPException(404, "patient not found")
        m = service.create_measurement(
            conn,
            patient_id=body.patient_id,
            biomarker_name=body.biomarker_name,
            value=body.value,
            measured_at=body.measured_at,
            treatment_id=body.treatment_id,
            modality=body.modality,
            unit=body.unit,
            notes=body.notes,
            created_by_user_id=_user_id(user),
        )
    return m.to_dict()


@router.post("/measurements/bulk")
def bulk_measurements(
    body: BulkMeasurementsIn,
    user: User | None = Depends(current_user),
) -> dict[str, Any]:
    if not body.measurements:
        raise HTTPException(400, "no measurements provided")
    records = [m.model_dump() for m in body.measurements]
    with get_conn() as conn:
        created = service.bulk_create_measurements(
            conn, records, created_by_user_id=_user_id(user)
        )
    return {"created": len(created), "ids": [m.id for m in created]}


@router.post("/measurements/csv")
async def upload_csv(
    file: UploadFile = File(...),
    user: User | None = Depends(current_user),
) -> dict[str, Any]:
    raw = await file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(400, "file is not UTF-8") from exc
    records, errors = service.parse_measurement_csv(text)
    if not records:
        raise HTTPException(400, {"errors": errors})
    with get_conn() as conn:
        created = service.bulk_create_measurements(
            conn, records, created_by_user_id=_user_id(user)
        )
    return {"created": len(created), "errors": errors}


@router.get("/patients/{patient_id}/measurements")
def list_measurements(patient_id: str, biomarker: str | None = None) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = service.list_measurements_for_patient(
            conn, patient_id, biomarker_name=biomarker
        )
    return [m.to_dict() for m in rows]


# ── Analysis / catalog ──────────────────────────────────────────────────────

@router.get("/peptides")
def peptides_with_data() -> list[dict[str, Any]]:
    with get_conn() as conn:
        return analysis.peptides_with_data(conn)


@router.get("/peptides/{peptide_name}/biomarkers")
def peptide_biomarker_catalog(peptide_name: str) -> list[dict[str, Any]]:
    with get_conn() as conn:
        return analysis.available_biomarkers(conn, peptide_name)


@router.get("/cohort")
def cohort(
    peptide: str,
    biomarker: str,
    dose_min: float | None = None,
    dose_max: float | None = None,
) -> dict[str, Any]:
    with get_conn() as conn:
        result = analysis.cohort_trajectories(
            conn,
            peptide_name=peptide,
            biomarker_name=biomarker,
            dose_min=dose_min,
            dose_max=dose_max,
        )
    return result.to_dict()


# ── Genetic profile + Bayesian predictions ──────────────────────────────────

@router.get("/patients/{patient_id}/genetics")
def get_genetics(patient_id: str) -> dict[str, Any]:
    with get_conn() as conn:
        if service.get_patient(conn, patient_id) is None:
            raise HTTPException(404, "patient not found")
        raw = service.get_genetic_profile_json(conn, patient_id)
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
    with get_conn() as conn:
        if service.get_patient(conn, patient_id) is None:
            raise HTTPException(404, "patient not found")
        import random
        rng = random.Random(seed) if seed is not None else random.Random()
        profile = generate_synthetic_profile(rng)
        service.set_genetic_profile(
            conn, patient_id, profile.to_json(), source="synthetic"
        )
    return {
        "profile": profile.to_dict(),
        "source": "synthetic",
    }


def _extract_enrichment(job_results: dict[str, Any]) -> dict[str, Any]:
    """Pull the responder-adapter feature signals out of a completed /analyze
    job, keyed by the exact ``ResponderContext.extra`` channel each adapter reads:

    - ``prs_profile`` — the polygenic-risk output (the PRS adapter reads
      ``trait_scores.systemic_inflammation``);
    - ``bpc157`` — the BPC-157 composite prediction, which the pipeline attaches
      to the BPC-157 entry of ``peptide_recommendations``.
    """
    enrichment: dict[str, Any] = {}
    prs = job_results.get("prs_profile")
    if isinstance(prs, dict):
        enrichment["prs_profile"] = prs
    recs = (
        (job_results.get("peptide_recommendations") or {}).get("recommendations")
        or []
    )
    for rec in recs:
        if isinstance(rec, dict) and rec.get("peptide_name") == "BPC-157":
            pred = rec.get("bpc157_prediction")
            if isinstance(pred, dict):
                enrichment["bpc157"] = pred
            break
    return enrichment


@router.post("/patients/from-job/{job_id}")
def create_patient_from_job(
    job_id: str,
    body: PatientFromJobIn | None = None,
    user: User | None = Depends(current_user),
) -> dict[str, Any]:
    """Create a tracking patient pre-populated from a completed /analyze job."""
    from api import get_completed_job_results, get_job_filename

    job_results = get_completed_job_results(job_id)
    if job_results is None:
        raise HTTPException(404, "job not found or not complete")

    payload = body or PatientFromJobIn()
    if payload.label:
        label = payload.label
    else:
        fname = get_job_filename(job_id) or job_id[:8]
        label = f"Patient from {fname}"[:64]

    with get_conn() as conn:
        patient = service.create_patient(
            conn,
            label=label,
            sex=payload.sex,
            birth_year=payload.birth_year,
            notes=payload.notes,
            created_by_user_id=_user_id(user),
        )
        profile = build_profile_from_job_results(job_results, job_id=job_id)
        service.set_genetic_profile(
            conn, patient.id, profile.to_json(), source=f"job:{job_id}"
        )
        # Persist pipeline enrichment (PRS profile + BPC-157 composite) so the
        # corresponding responder adapters can fire at predict time. These are
        # computed over the full annotated genome and are not in the tracking
        # GeneticProfile, so they can only be captured here, from the job.
        enrichment = _extract_enrichment(job_results)
        if enrichment:
            service.set_patient_enrichment(
                conn, patient.id, json.dumps(enrichment)
            )

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
    with get_conn() as conn:
        if service.get_patient(conn, patient_id) is None:
            raise HTTPException(404, "patient not found")
        return analysis.predict_response(
            conn,
            patient_id=patient_id,
            peptide_name=peptide,
            biomarker_name=biomarker,
        )


@router.get("/patients/{patient_id}/priors")
def get_priors(patient_id: str) -> dict[str, Any]:
    """All per-peptide responder-strength priors derived from the patient's
    genetic profile."""
    with get_conn() as conn:
        if service.get_patient(conn, patient_id) is None:
            raise HTTPException(404, "patient not found")
        raw = service.get_genetic_profile_json(conn, patient_id)
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
    with get_conn() as conn:
        # Refuse the destructive force-wipe against a real (Postgres) database.
        # `force=True` FK-cascade-deletes and reseeds; that must never be
        # reachable in production, where the tracking store is Postgres. Additive
        # seeding, and force against the local SQLite dev DB, stay allowed.
        if body.force and getattr(conn, "_is_pg", False):
            raise HTTPException(
                status_code=403,
                detail="Refusing force-reseed against a Postgres database "
                       "(production). Force-wipe is dev/SQLite only.",
            )
        stats = run_seed(
            conn,
            rng=random.Random(body.seed),
            n_patients=body.patients,
            force=body.force,
        )
    return stats
