"""Legacy single-destination API model; signing secrets remain encrypted."""

from uuid import UUID

from sqlalchemy import Column, LargeBinary, UniqueConstraint
from sqlmodel import Field

from app.models.base import BaseMixin


class EventDestination(BaseMixin, table=True):
    """Compatibility model for the current one-destination-per-merchant API."""

    __table_args__ = (UniqueConstraint("merchant_id", name="uq_event_destination_merchant"),)

    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    url: str = Field(max_length=512)
    signing_secret_ciphertext: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
    enabled: bool = Field(default=True, nullable=False, index=True)
