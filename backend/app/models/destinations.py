"""Merchant-owned webhook destinations; signing secrets are encrypted."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, LargeBinary, UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EventDestination(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("merchant_id", name="uq_event_destination_merchant"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    url: str = Field(max_length=512)
    signing_secret_ciphertext: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
    enabled: bool = Field(default=True, nullable=False, index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)
