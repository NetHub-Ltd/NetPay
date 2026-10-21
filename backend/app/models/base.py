"""Shared persistence primitives for NetPay SQLModel tables."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Return the current timezone-aware UTC instant."""
    return datetime.now(UTC)


def require_aware_utc(value: datetime) -> datetime:
    """Normalize an aware datetime to UTC and reject ambiguous naive values."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("NetPay timestamps must be timezone-aware")
    return value.astimezone(UTC)


class BaseMixin(SQLModel):
    """Provide shared identity, UTC timestamps, and soft-deletion behavior.

    Table models inherit these fields and lifecycle methods. Use SQLModel's
    sa_type mapping instead of sharing SQLAlchemy Column instances across
    tables; each inheriting table must receive its own independent columns.
    Queries must still explicitly exclude soft-deleted rows.
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
    # NULL denotes active. Financial evidence must not expose ordinary deletion.
    deleted_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        nullable=True,
    )

    def soft_delete(self, when: datetime | None = None) -> None:
        """Mark a mutable record deleted without removing its database row.

        Immutable financial evidence and audit records should prohibit this
        operation at their service boundary even though they share this mixin.
        """
        self.deleted_at = require_aware_utc(when) if when is not None else utc_now()
        self.updated_at = utc_now()

    def restore(self) -> None:
        """Restore a soft-deleted mutable record and refresh its update time."""
        self.deleted_at = None
        self.updated_at = utc_now()

    @property
    def is_deleted(self) -> bool:
        """Return whether this record is soft-deleted."""
        return self.deleted_at is not None
