"""Canonical payments, idempotency keys, and provider callback evidence."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Column, DateTime, JSON, CheckConstraint, UniqueConstraint
from sqlmodel import Field

from app.models.base import BaseMixin, utc_now


class Payment(BaseMixin, table=True):
    """Merchant-owned payment intent and verified outcome.

    A successful STK initiation is not proof of payment success. Amounts are
    stored as integer minor units, never floating-point values.
    """

    __tablename__ = "payment"
    __table_args__ = (
        UniqueConstraint("merchant_id", "merchant_reference", name="uq_payment_merchant_reference"),
        UniqueConstraint("integration_id", "provider_receipt", name="uq_payment_integration_provider_receipt"),
        UniqueConstraint("integration_id", "provider_checkout_request_id", name="uq_payment_integration_checkout"),
        UniqueConstraint("integration_id", "provider_merchant_request_id", name="uq_payment_integration_merchant_request"),
        CheckConstraint("amount_minor > 0", name="ck_payment_amount_positive"),
    )

    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    integration_id: UUID = Field(foreign_key="providerintegration.id", index=True)
    merchant_reference: str = Field(max_length=120)
    amount_minor: int = Field(gt=0)
    currency: str = Field(default="KES", min_length=3, max_length=3)
    phone_number: str | None = Field(default=None, max_length=20)
    payment_source: str = Field(default="stk", max_length=16, index=True)
    direction: str = Field(default="inbound", max_length=16)
    description: str | None = Field(default=None, max_length=250)
    status: str = Field(default="pending", max_length=32, index=True)
    provider_transaction_id: str | None = Field(default=None, max_length=120, index=True)
    provider_checkout_request_id: str | None = Field(default=None, max_length=120, index=True)
    provider_merchant_request_id: str | None = Field(default=None, max_length=120, index=True)
    provider_receipt: str | None = Field(default=None, max_length=64, index=True)
    provider_result_code: str | None = Field(default=None, max_length=32)
    provider_result_description: str | None = Field(default=None, max_length=250)
    initiated_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    completed_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    succeeded_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    failed_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    cancelled_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))


class IdempotencyRecord(BaseMixin, table=True):
    """Stable request identity preventing duplicate merchant operations."""

    __tablename__ = "idempotencyrecord"
    __table_args__ = (UniqueConstraint("merchant_id", "key", name="uq_idempotency_merchant_key"),)

    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    client_id: UUID | None = Field(default=None, foreign_key="m2mclient.id", index=True)
    key: str = Field(max_length=160)
    request_hash: str = Field(max_length=64)
    resource_id: UUID | None = Field(default=None, index=True)
    response_status: int | None = Field(default=None)
    response_snapshot: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    expires_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True), index=True)


class ProviderCallback(BaseMixin, table=True):
    """Deduplicated callback evidence; payloads must be minimized and sanitized."""

    __tablename__ = "providercallback"
    __table_args__ = (
        UniqueConstraint("integration_id", "provider_event_id", name="uq_callback_integration_event"),
        UniqueConstraint("integration_id", "dedupe_fingerprint", name="uq_callback_integration_fingerprint"),
    )

    integration_id: UUID = Field(foreign_key="providerintegration.id", index=True)
    provider_event_id: str = Field(max_length=120)
    merchant_id: UUID | None = Field(default=None, foreign_key="merchant.id", index=True)
    payment_id: UUID | None = Field(default=None, foreign_key="payment.id", index=True)
    callback_type: str = Field(default="stk", max_length=32, index=True)
    dedupe_fingerprint: str = Field(max_length=64)
    provider_transaction_id: str | None = Field(default=None, max_length=120, index=True)
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    processing_status: str = Field(default="received", max_length=24, index=True)
    processing_error: str | None = Field(default=None, max_length=500)
    received_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True), nullable=False)
    processed_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
