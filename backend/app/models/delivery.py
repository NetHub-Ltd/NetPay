"""Append-only delivery attempt history for outbound events."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EventDeliveryAttempt(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("outbox_event_id", "attempt_number", name="uq_delivery_attempt_number"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    outbox_event_id: UUID = Field(foreign_key="eventoutbox.id", index=True)
    attempt_number: int = Field(nullable=False)
    outcome: str = Field(max_length=24, index=True)
    http_status: int | None = Field(default=None)
    safe_error_code: str | None = Field(default=None, max_length=100)
    duration_ms: int = Field(default=0, nullable=False)
    attempted_at: datetime = Field(default_factory=utc_now, nullable=False)
