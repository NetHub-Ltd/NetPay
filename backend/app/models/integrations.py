"""Merchant-owned Daraja credentials and callback configuration."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, LargeBinary, UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DarajaIntegration(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("merchant_id", "shortcode", "environment", name="uq_integration_merchant_shortcode_env"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    integration_id: str = Field(max_length=64, unique=True, index=True)
    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    environment: str = Field(max_length=16)
    shortcode: str = Field(max_length=32, index=True)
    product_type: str = Field(max_length=24)
    consumer_key_ciphertext: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
    consumer_secret_ciphertext: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
    passkey_ciphertext: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
    credential_status: str = Field(default="pending", max_length=24, index=True)
    c2b_enabled: bool = Field(default=False, nullable=False)
    c2b_registration_status: str = Field(default="not_requested", max_length=24)
    stk_callback_url: str = Field(max_length=512)
    c2b_validation_url: str = Field(max_length=512)
    c2b_confirmation_url: str = Field(max_length=512)
    registration_error: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)
