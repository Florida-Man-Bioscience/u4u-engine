"""
Tests for HealthKit ingestion (engine/health).

Two layers:
  * Pure tests (no database) — schema alias parsing + token hashing.
  * Integration tests — require a live Postgres via DATABASE_URL; skipped otherwise.
"""
from __future__ import annotations

import os
import uuid

import pytest

from engine.health.auth import hash_token
from engine.health.schemas import UploadBody

# ── Pure tests (no DB) ────────────────────────────────────────────────────────


def test_upload_body_parses_camelcase_app_payload():
    body = UploadBody(
        samples=[
            {
                "uuid": str(uuid.uuid4()),
                "typeIdentifier": "HKQuantityTypeIdentifierStepCount",
                "kind": "quantity",
                "startDate": "2026-01-01T00:00:00Z",
                "endDate": "2026-01-01T00:01:00Z",
                "value": 100.0,
                "unit": "count",
                "sourceName": "Apple Watch",
                "sourceBundleIdentifier": "com.apple.health",
                "isDeleted": False,
            }
        ]
    )
    sample = body.samples[0]
    assert sample.type_identifier == "HKQuantityTypeIdentifierStepCount"
    assert sample.source_bundle_identifier == "com.apple.health"
    assert sample.value == 100.0
    assert sample.is_deleted is False
    assert sample.start_date.year == 2026


def test_upload_body_parses_nested_workout():
    body = UploadBody(
        samples=[
            {
                "uuid": str(uuid.uuid4()),
                "typeIdentifier": "HKWorkoutTypeIdentifier",
                "kind": "workout",
                "startDate": "2026-01-01T00:00:00Z",
                "endDate": "2026-01-01T00:30:00Z",
                "workout": {
                    "activityType": 37,
                    "durationSeconds": 1800.0,
                    "totalEnergyKilocalories": 250.0,
                    "totalDistanceMeters": 5000.0,
                },
            }
        ]
    )
    workout = body.samples[0].workout
    assert workout is not None
    assert workout.activity_type == 37
    assert workout.total_distance_meters == 5000.0


def test_hash_token_is_deterministic_and_hex():
    h = hash_token("pep_example")
    assert h == hash_token("pep_example")
    assert len(h) == 64
    assert hash_token("pep_example") != hash_token("pep_other")


# ── Integration tests (require Postgres) ──────────────────────────────────────

_DB_ENABLED = bool(os.getenv("DATABASE_URL", "").strip())
pytestmark_integration = pytest.mark.skipif(
    not _DB_ENABLED, reason="DATABASE_URL not set — Postgres integration test skipped."
)


@pytestmark_integration
@pytest.mark.asyncio
async def test_ingest_is_idempotent_by_uuid():
    import secrets

    from httpx import ASGITransport, AsyncClient
    from sqlalchemy import delete

    from api import app
    from engine.health.db import init_models, session_factory
    from engine.health.models import DeviceToken, HealthSample, User

    await init_models()

    raw_token = "pep_" + secrets.token_urlsafe(16)
    email = f"test-{uuid.uuid4()}@example.com"
    sample_uuid = str(uuid.uuid4())

    async with session_factory()() as session:
        user = User(email=email)
        session.add(user)
        await session.flush()
        session.add(DeviceToken(user_id=user.id, token_hash=hash_token(raw_token)))
        await session.commit()
        user_id = user.id

    payload = {
        "samples": [
            {
                "uuid": sample_uuid,
                "typeIdentifier": "HKQuantityTypeIdentifierStepCount",
                "kind": "quantity",
                "startDate": "2026-01-01T00:00:00Z",
                "endDate": "2026-01-01T00:01:00Z",
                "value": 100.0,
                "unit": "count",
                "isDeleted": False,
            }
        ]
    }
    headers = {"Authorization": f"Bearer {raw_token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.post("/health-samples", json=payload, headers=headers)
        assert r1.status_code == 200
        assert r1.json()["received"] == 1

        # Re-deliver the same sample — must upsert, not duplicate.
        r2 = await client.post("/health-samples", json=payload, headers=headers)
        assert r2.status_code == 200

        summary = await client.get("/health-samples/summary", headers=headers)
        assert summary.json()["sample_count"] == 1

        # No/invalid token → 401.
        bad = await client.post("/health-samples", json=payload, headers={"Authorization": "Bearer nope"})
        assert bad.status_code == 401

    # Cleanup.
    async with session_factory()() as session:
        await session.execute(delete(HealthSample).where(HealthSample.user_id == user_id))
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()
