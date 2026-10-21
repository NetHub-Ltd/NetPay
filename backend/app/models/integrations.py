"""Merchant-owned Daraja credentials and callback configuration."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, DateTime, LargeBinary, UniqueConstraint
from sqlmodel import Field

from app.models.base import BaseMixin


class DarajaIntegration(BaseMixin, table=True):
    """Configuration boundary for one merchant/provider environment.

    The opaque integration ID routes callbacks; it is not an authentication
    token. Credentials are encrypted before they reach these binary columns.
    """

    __table_args__ = (
        UniqueConstraint("merchant_id", "shortcode", "environment", name="uq_integration_merchant_shortcode_env"),
    )

    integration_id: str = Field(max_length=64, unique=True, index=True)
    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    environment: str = Field(max_length=16)
    shortcode: str = Field(max_length=32, index=True)
    party_b_shortcode: str = Field(max_length=32)
    product_type: str = Field(max_length=24)
    consumer_key_ciphertext: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
    consumer_secret_ciphertext: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
    passkey_ciphertext: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
    credential_status: str = Field(default="pending", max_length=24, index=True)
    credentials_validated_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    credential_version: int = Field(default=1, ge=1, nullable=False)
    c2b_enabled: bool = Field(default=False, nullable=False)
    c2b_registration_status: str = Field(default="not_requested", max_length=24)
    stk_callback_url: str = Field(max_length=512)
    c2b_validation_url: str = Field(max_length=512)
    c2b_confirmation_url: str = Field(max_length=512)
    c2b_registered_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    registration_error: str | None = Field(default=None, max_length=500)
