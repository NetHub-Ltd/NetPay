"""Daraja integration configuration and encrypted credential material."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, LargeBinary, UniqueConstraint
from sqlmodel import Field

from app.models.base import BaseMixin


class DarajaIntegration(BaseMixin, table=True):
    """One merchant's Daraja environment, shortcode, credentials, and callback URLs.

    Credential fields contain ciphertext only. Optional setup fields allow an
    integration to exist in a pending state; application logic must validate
    required Daraja configuration before enabling payment initiation.
    """

    __tablename__ = "providerintegration"
    __table_args__ = (
        UniqueConstraint("merchant_id", "provider", "environment", name="uq_integration_provider_environment"),
        UniqueConstraint("integration_id", name="uq_providerintegration_integration_id"),
    )

    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    provider: str = Field(default="daraja", max_length=32)
    environment: str = Field(default="sandbox", max_length=16)
    status: str = Field(default="pending", max_length=24)
    credentials_ciphertext: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    credential_reference: str | None = Field(default=None, max_length=255)
    integration_id: str = Field(default_factory=lambda: f"int_{uuid4().hex}", max_length=64)
    shortcode: str | None = Field(default=None, max_length=32, index=True)
    party_b_shortcode: str | None = Field(default=None, max_length=32)
    product_type: str | None = Field(default=None, max_length=24)
    consumer_key_ciphertext: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    consumer_secret_ciphertext: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    passkey_ciphertext: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    credential_status: str = Field(default="pending", max_length=24, index=True)
    credentials_validated_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    credential_version: int = Field(default=1, ge=1)
    c2b_enabled: bool = Field(default=False)
    c2b_registration_status: str = Field(default="not_requested", max_length=24)
    stk_callback_url: str | None = Field(default=None, max_length=512)
    c2b_validation_url: str | None = Field(default=None, max_length=512)
    c2b_confirmation_url: str | None = Field(default=None, max_length=512)
    c2b_registered_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    registration_error: str | None = Field(default=None, max_length=500)
