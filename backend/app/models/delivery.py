"""Append-only history of outbound webhook delivery attempts."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, UniqueConstraint
from sqlmodel import Field

from app.models.base import BaseMixin, utc_now


class EventDeliveryAttempt(BaseMixin, table=True):
    """Record one delivery attempt without overwriting prior outcomes."""

    __tablename__ = "eventdeliveryattempt"
    __table_args__ = (UniqueConstraint("event_delivery_id", "attempt_number", name="uq_delivery_attempt_number"),)

    event_delivery_id: UUID = Field(foreign_key="eventdelivery.id", index=True)
    attempt_number: int = Field(ge=1)
    status: str = Field(max_length=32, index=True)
    attempted_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True), nullable=False)
    completed_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    http_status: int | None = Field(default=None)
    response_excerpt: str | None = Field(default=None, max_length=500)
    error_code: str | None = Field(default=None, max_length=100)
