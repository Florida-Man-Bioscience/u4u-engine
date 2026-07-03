"""
engine/health/models.py
=======================
SQLAlchemy 2.0 ORM models for HealthKit ingestion.

    app_users       — one row per app account (email identity for now); distinct
                      from the platform operator `users` table (engine/users)
    device_tokens   — long-lived opaque bearer tokens (stored hashed) → app_user
    health_samples  — one row per HealthKit sample, mirroring the iOS app's
                      PendingSamplePayload. Composite PK (user_id, uuid) makes
                      re-delivered samples an idempotent upsert.

Mirrors db/models/peptide_models.py conventions (DeclarativeBase, Mapped[]).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for the HealthKit ingestion tables."""


class User(Base):
    # NOTE: table is `app_users`, NOT `users`. The platform's `users` table
    # (engine/users, Authentik-backed operators) is a different population;
    # this is the peptodyssey app's end-user accounts.
    __tablename__ = "app_users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    tokens: Mapped[list["DeviceToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class DeviceToken(Base):
    __tablename__ = "device_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_users.id", ondelete="CASCADE"), nullable=False
    )
    # SHA-256 hex of the raw token — the raw value is shown once at creation.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    device_name: Mapped[str | None] = mapped_column(Text)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="tokens")


class HealthSample(Base):
    __tablename__ = "health_samples"

    # Composite PK: a sample UUID is unique per user, so re-delivery upserts.
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    uuid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)

    type_identifier: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False)

    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(Text)
    category_value: Mapped[int | None] = mapped_column(Integer)

    source_name: Mapped[str | None] = mapped_column(Text)
    source_bundle_identifier: Mapped[str | None] = mapped_column(Text)
    device_name: Mapped[str | None] = mapped_column(Text)

    workout: Mapped[dict | None] = mapped_column(JSONB)
    sample_metadata: Mapped[dict | None] = mapped_column(JSONB)

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
