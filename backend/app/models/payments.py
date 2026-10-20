"""Durable payment state and provider callback records."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON, CheckConstraint, UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Payment(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint("amount_minor > 0", name="ck_payment_amount_positive"),
        UniqueConstraint("integration_id", "provider_receipt", name="uq_payment_integration_provider_receipt"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    integration_id: UUID = Field(foreign_key="darajaintegration.id", index=True)
    client_reference: str = Field(max_length=100)
    amount_minor: int = Field(gt=0)
    currency: str = Field(default="KES", max_length=3)
    phone_number: str | None = Field(default=None, max_length=20, nullable=True)
    payment_source: str = Field(default="stk", max_length=16, index=True)
    status: str = Field(default="pending", max_length=24, index=True)
    provider_checkout_request_id: str | None = Field(default=None, max_length=120, index=True)
    provider_merchant_request_id: str | None = Field(default=None, max_length=120, index=True)
    provider_receipt: str | None = Field(default=None, max_length=64, index=True)
    provider_result_code: str | None = Field(default=None, max_length=32)
    provider_result_description: str | None = Field(default=None, max_length=250)
    initiated_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)


class IdempotencyRecord(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("merchant_id", "key", name="uq_idempotency_merchant_key"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    key: str = Field(max_length=200)
    request_hash: str = Field(max_length=64)
    resource_id: UUID | None = Field(default=None, index=True)
    response_status: int | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    expires_at: datetime | None = Field(default=None, index=True)


class ProviderCallback(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("integration_id", "dedupe_fingerprint", name="uq_callback_integration_fingerprint"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    integration_id: UUID = Field(foreign_key="darajaintegration.id", index=True)
    payment_id: UUID | None = Field(default=None, foreign_key="payment.id", index=True)
    callback_type: str = Field(max_length=32, index=True)
    dedupe_fingerprint: str = Field(max_length=64)
    safe_payload: dict[str, object] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    processing_status: str = Field(default="received", max_length=24, index=True)
    received_at: datetime = Field(default_factory=utc_now, nullable=False)
    processed_at: datetime | None = Field(default=None)
