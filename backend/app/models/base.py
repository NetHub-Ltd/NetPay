"""Shared persistence primitives for NetPay SQLModel tables."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Return the current timezone-aware UTC instant."""
    return datetime.now(UTC)


class BaseMixin(SQLModel):
    """Provide stable identity, UTC timestamps, and soft-deletion metadata.

    Table models inherit these fields. This mixin does not automatically hide
    soft-deleted rows or authorize deletion; query and service boundaries must
    enforce those policies explicitly.
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, onupdate=utc_now),
    )
    # NULL denotes an active record. Financial evidence is not deletable merely
    # because it has this shared field; service policy controls its lifecycle.
    deleted_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
