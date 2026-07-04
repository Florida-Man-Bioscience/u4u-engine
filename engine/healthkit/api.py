"""
engine/healthkit/api.py
======================
FastAPI router for HealthKit ingestion from the peptodyssey iOS app.

Mount in api.py via:
    from engine.healthkit.api import router as healthkit_router
    app.include_router(healthkit_router)

Auth: an interim per-device bearer token (engine/healthkit/auth.py), required
whenever a real database is configured (fail-closed in prod), open only in the
local SQLite dev/test fallback. `current_user` (Authentik forward-auth) is still
read for the operator audit note when present. Data is de-identified — subjects
are the app-assigned opaque `subject_id`, never the Authentik user. The
longer-term auth target is Authentik device-code flow (see docs/healthkit-storage.md).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from engine.users.deps import current_user
from engine.users.models import User

from . import service
from .auth import enforce_subject, require_device_token
from .db import get_conn
from .schemas import IngestBody, IngestResult

router = APIRouter(prefix="/healthkit", tags=["healthkit"])


@router.post("/samples", response_model=IngestResult)
def ingest_samples(
    body: IngestBody,
    token: dict | None = Depends(require_device_token),
    user: User | None = Depends(current_user),
) -> IngestResult:
    """Idempotent batch upload of HealthKit samples (insert-only by sample uuid)."""
    enforce_subject(token, body.subject_id)

    note_parts = []
    if token is not None:
        # Always attribute an authenticated write: label if set, else a token
        # hash prefix so the audit row is never anonymous when a token was used.
        note_parts.append(f"token={token.get('label') or token['token_hash'][:12]}")
    if user is not None:
        note_parts.append(f"authentik_uid={user.authentik_uid}")
    notes = "; ".join(note_parts) or None

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
    token: dict | None = Depends(require_device_token),
) -> list[dict]:
    """Read back a subject's samples (optionally filtered by type / since)."""
    # Reads require a subject-bound token: an unbound token must not be able to
    # read arbitrary subjects' data.
    enforce_subject(token, subject_id, require_bound=True)
    with get_conn() as conn:
        return service.read_samples(
            conn,
            subject_id=subject_id,
            type_identifier=type,
            since=since,
            limit=limit,
        )
