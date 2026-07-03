"""
engine/health/schemas.py
=======================
Pydantic request models for HealthKit ingestion.

The iOS app encodes camelCase JSON keys (e.g. ``typeIdentifier``,
``sourceBundleIdentifier``) with ISO-8601 dates. These models accept that shape
via an alias generator while exposing snake_case attributes to Python.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="ignore")


class WorkoutInfo(BaseModel):
    model_config = _config

    activity_type: int
    duration_seconds: float
    total_energy_kilocalories: float | None = None
    total_distance_meters: float | None = None


class SamplePayload(BaseModel):
    model_config = _config

    uuid: UUID
    type_identifier: str
    kind: str
    start_date: datetime
    end_date: datetime
    value: float | None = None
    unit: str | None = None
    category_value: int | None = None
    source_name: str | None = None
    source_bundle_identifier: str | None = None
    device_name: str | None = None
    workout: WorkoutInfo | None = None
    metadata: dict[str, str] | None = None
    is_deleted: bool = False


class UploadBody(BaseModel):
    model_config = _config

    samples: list[SamplePayload]
