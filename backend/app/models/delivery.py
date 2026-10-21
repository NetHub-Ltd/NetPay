"""Append-only delivery attempt history for outbound events."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from app.models.base import BaseMixin, utc_now


class EventDeliveryAttempt(BaseMixin, table=True):
    """Record one HTTP delivery attempt without overwriting prior outcomes.

    outbox_event_id remains for compatibility with the existing worker.
    New endpoint-specific delivery flows also populate event_delivery_id.
    """

    __table_args__ = (
        UniqueConstraint("outbox_event_id", "attempt_number", name="uq_delivery_attempt_number"),
    )

    outbox_event_id: UUID = Field(foreign_key="eventoutbox.id", index=True)
    event_delivery_id: UUID | None = Field(default=None, foreign_key="eventdelivery.id", index=True)
    attempt_number: int = Field(ge=1, nullable=False)
    outcome: str = Field(max_length=24, index=True)
    http_status: int | None = Field(default=None)
    safe_error_code: str | None = Field(default=None, max_length=100)
    duration_ms: int = Field(default=0, ge=0, nullable=False)
    attempted_at: datetime = Field(default_factory=utc_now, nullable=False)
