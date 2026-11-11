"""Shared identity and lifecycle primitives for persisted NetPay records."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Return the current timezone-aware UTC instant."""
    return datetime.now(UTC)


def require_aware_utc(value: datetime) -> datetime:
    """Normalize an aware timestamp to UTC and reject ambiguous naive values."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("NetPay timestamps must be timezone-aware")
    return value.astimezone(UTC)


class BaseMixin(SQLModel):
    """Provide UUID identity and UTC-aware lifecycle timestamps to table models."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True), nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": utc_now},
        nullable=False,
    )
    deleted_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
