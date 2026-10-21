"""Transactional outbox records for durable payment event delivery."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, JSON, UniqueConstraint
from sqlmodel import Field

from app.models.base import BaseMixin, utc_now


class EventOutbox(BaseMixin, table=True):
    """Durable event written in the same transaction as its domain change."""

    __table_args__ = (UniqueConstraint("event_id", name="uq_eventoutbox_event_id"),)

    event_id: UUID = Field(default_factory=uuid4, index=True)
    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    aggregate_type: str = Field(default="payment", max_length=50)
    aggregate_id: UUID = Field(index=True)
    event_type: str = Field(max_length=100, index=True)
    schema_version: int = Field(default=1, ge=1, nullable=False)
    payload: dict[str, object] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    delivery_status: str = Field(default="pending", max_length=24, index=True)
    attempts: int = Field(default=0, ge=0, nullable=False)
    next_attempt_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True), index=True, nullable=False)
    last_error_code: str | None = Field(default=None, max_length=100)
    published_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    delivered_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
