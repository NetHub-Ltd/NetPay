"""Transactional outbox records for durable payment-event publication."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, JSON, UniqueConstraint
from sqlmodel import Field

from app.models.base import BaseMixin, utc_now


class EventOutbox(BaseMixin, table=True):
    """Durable event committed in the same transaction as its domain change."""

    __tablename__ = "eventoutbox"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_eventoutbox_event_id"),
        CheckConstraint("attempt_count >= 0", name="ck_eventoutbox_attempt_count_nonnegative"),
    )

    event_id: UUID = Field(default_factory=uuid4)
    merchant_id: UUID | None = Field(default=None, foreign_key="merchant.id", index=True)
    aggregate_type: str = Field(default="payment", max_length=50)
    aggregate_id: UUID = Field(index=True)
    event_type: str = Field(max_length=100, index=True)
    schema_version: int = Field(default=1, ge=1)
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    occurred_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True), nullable=False)
    published_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True), index=True)
    attempt_count: int = Field(default=0, ge=0)
