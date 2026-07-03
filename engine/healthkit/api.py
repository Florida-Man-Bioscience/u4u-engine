"""
engine/healthkit/api.py
======================
FastAPI router for HealthKit ingestion from the peptodyssey iOS app.

Mount in api.py via:
    from engine.healthkit.api import router as healthkit_router
    app.include_router(healthkit_router)

Auth: soft `current_user` (same pattern as /analyze). In prod the Authentik
proxy stamps headers and the operator is recorded in the ingestion audit; in dev
(no proxy) it's None and ingestion still works. Data is de-identified — subjects
are the app-assigned opaque `subject_id`, not the Authentik user.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from engine.users.deps import current_user
from engine.users.models import User

from . import service
from .db import get_conn
from .schemas import IngestBody, IngestResult

router = APIRouter(prefix="/healthkit", tags=["healthkit"])


@router.post("/samples", response_model=IngestResult)
def ingest_samples(
    body: IngestBody,
    user: User | None = Depends(current_user),
) -> IngestResult:
    """Idempotent batch upload of HealthKit samples (insert-only by sample uuid)."""
    notes = f"authentik_uid={user.authentik_uid}" if user is not None else None
    source_name = None
    for s in body.samples:
        if s.source and s.source.name:
            source_name = s.source.name
            break

    with get_conn() as conn:
        received, inserted = service.ingest(
            conn,
            subject_id=body.subject_id,
            samples=body.samples,
            anchors=body.anchors,
            source_name=source_name,
            notes=notes,
        )
    return IngestResult(received=received, inserted=inserted)


@router.get("/samples")
def read_samples(
    subject_id: str = Query(..., min_length=1),
    type: str | None = Query(default=None),
    since: str | None = Query(default=None, description="ISO-8601; start_time >= since"),
    limit: int = Query(default=1000, ge=1, le=10000),
    user: User | None = Depends(current_user),
) -> list[dict]:
    """Read back a subject's samples (optionally filtered by type / since)."""
    with get_conn() as conn:
        return service.read_samples(
            conn,
            subject_id=subject_id,
            type_identifier=type,
            since=since,
            limit=limit,
        )
