"""Transactional outbox records for durable payment event delivery."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EventOutbox(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    event_id: UUID = Field(default_factory=uuid4, unique=True, index=True)
    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    aggregate_id: UUID = Field(index=True)
    event_type: str = Field(max_length=100, index=True)
    schema_version: int = Field(default=1, nullable=False)
    payload: dict[str, object] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    delivery_status: str = Field(default="pending", max_length=24, index=True)
    attempts: int = Field(default=0, nullable=False)
    next_attempt_at: datetime = Field(default_factory=utc_now, index=True, nullable=False)
    last_error_code: str | None = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    delivered_at: datetime | None = Field(default=None)
