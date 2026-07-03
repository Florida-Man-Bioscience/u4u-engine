"""Dataclasses for the tracking domain."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Patient:
    id: str
    label: str
    sex: str | None
    birth_year: int | None
    notes: str | None
    created_at: str
    created_by_user_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Treatment:
    id: str
    patient_id: str
    peptide_name: str
    dose: float | None
    dose_unit: str | None
    schedule: str | None
    route: str | None
    start_date: str
    end_date: str | None
    notes: str | None
    created_at: str
    created_by_user_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Measurement:
    id: str
    patient_id: str
    treatment_id: str | None
    biomarker_name: str
    modality: str | None
    value: float
    unit: str | None
    measured_at: str
    notes: str | None
    created_at: str
    created_by_user_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
