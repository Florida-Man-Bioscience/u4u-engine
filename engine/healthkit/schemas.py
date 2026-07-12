"""
engine/healthkit/schemas.py
==========================
Pydantic request/response bodies for HealthKit ingestion. Matches the contract
in docs/healthkit-storage.md: camelCase-ish keys, `class` aliased (reserved
word), ISO-8601 datetimes.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

_config = ConfigDict(populate_by_name=True, extra="ignore")


class SourceIn(BaseModel):
    model_config = _config
    name: str | None = None
    bundleId: str | None = None


class WorkoutIn(BaseModel):
    model_config = _config
    activity_type: str | None = Field(default=None, alias="activityType")
    duration_s: float | None = Field(default=None, alias="durationSeconds")
    total_energy_kcal: float | None = Field(default=None, alias="totalEnergyKcal")
    total_distance_m: float | None = Field(default=None, alias="totalDistanceMeters")


class SampleIn(BaseModel):
    model_config = _config

    uuid: UUID
    cls: str = Field(alias="class")
    type: str
    value: float | None = None
    unit: str | None = None
    start: datetime
    end: datetime
    source: SourceIn | None = None
    device: dict | None = None
    metadata: dict = Field(default_factory=dict)
    workout: WorkoutIn | None = None


class IngestBody(BaseModel):
    model_config = _config

    # Accept the iOS-natural camelCase `subjectId` as well as `subject_id`
    # (populate_by_name=True). The rest of the payload is already camelCase
    # (class/bundleId/activityType), so subject_id was the lone snake-only key.
    subject_id: str = Field(min_length=1, max_length=128, alias="subjectId")
    samples: list[SampleIn]
    # Optional per-type HKQueryAnchor mirror (base64), type_identifier -> anchor.
    anchors: dict[str, str] | None = None


class IngestResult(BaseModel):
    received: int
    inserted: int


class EnrollBody(BaseModel):
    model_config = _config

    subject_id: str = Field(min_length=1, max_length=128, alias="subjectId")
    code: str = Field(min_length=1, max_length=128)


class EnrollResult(BaseModel):
    model_config = _config

    # The raw device token, returned once; the app stores it in the Keychain.
    token: str
    subject_id: str = Field(serialization_alias="subjectId")
