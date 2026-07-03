"""
engine/health/api.py
===================
FastAPI router for HealthKit ingestion. Mounted by api.py.

Endpoints (unprefixed here; the production reverse proxy exposes them under
/api/v1/*, matching the rest of the engine):

    POST /health-samples          — idempotent upsert of a batch of samples
    GET  /health-samples/summary  — sample count for the authenticated user
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from engine.health.auth import current_user_id
from engine.health.db import get_session
from engine.health.models import HealthSample
from engine.health.schemas import SamplePayload, UploadBody

router = APIRouter(tags=["healthkit"])

# Columns refreshed when an existing (user_id, uuid) row is re-delivered.
_UPSERT_COLUMNS = (
    "type_identifier",
    "kind",
    "start_date",
    "end_date",
    "value",
    "unit",
    "category_value",
    "source_name",
    "source_bundle_identifier",
    "device_name",
    "workout",
    "sample_metadata",
    "is_deleted",
)


def _row(user_id: UUID, sample: SamplePayload) -> dict:
    return {
        "user_id": user_id,
        "uuid": sample.uuid,
        "type_identifier": sample.type_identifier,
        "kind": sample.kind,
        "start_date": sample.start_date,
        "end_date": sample.end_date,
        "value": sample.value,
        "unit": sample.unit,
        "category_value": sample.category_value,
        "source_name": sample.source_name,
        "source_bundle_identifier": sample.source_bundle_identifier,
        "device_name": sample.device_name,
        "workout": sample.workout.model_dump() if sample.workout else None,
        "sample_metadata": sample.metadata,
        "is_deleted": sample.is_deleted,
    }


@router.post("/health-samples")
async def ingest_health_samples(
    body: UploadBody,
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Upsert a batch of samples by (user_id, uuid). Idempotent: re-delivered
    samples update in place, so the client's at-least-once delivery is safe."""
    if not body.samples:
        return {"received": 0}

    stmt = pg_insert(HealthSample).values([_row(user_id, s) for s in body.samples])
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "uuid"],
        set_={col: getattr(stmt.excluded, col) for col in _UPSERT_COLUMNS},
    )
    await session.execute(stmt)
    await session.commit()
    return {"received": len(body.samples)}


@router.get("/health-samples/summary")
async def health_samples_summary(
    user_id: UUID = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Total sample count stored for the authenticated user."""
    total = await session.scalar(
        select(func.count()).select_from(HealthSample).where(HealthSample.user_id == user_id)
    )
    return {"user_id": str(user_id), "sample_count": total or 0}
