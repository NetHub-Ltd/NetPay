"""Canonical payment state, idempotency, and provider callback evidence."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, Column, CheckConstraint, UniqueConstraint
from sqlmodel import Field

from app.models.base import BaseMixin, utc_now


class Payment(BaseMixin, table=True):
    """Merchant-owned payment intent and canonical verified outcome.

    Provider acceptance is not payment success. Ambiguous provider outcomes
    remain unresolved until callback or verification evidence is sufficient.
    Amounts are integer minor units, never binary floating-point values.
    """

    __table_args__ = (
        CheckConstraint("amount_minor > 0", name="ck_payment_amount_positive"),
        UniqueConstraint("integration_id", "provider_receipt", name="uq_payment_integration_provider_receipt"),
        UniqueConstraint("integration_id", "provider_checkout_request_id", name="uq_payment_integration_checkout"),
        UniqueConstraint("integration_id", "provider_merchant_request_id", name="uq_payment_integration_merchant_request"),
    )

    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    integration_id: UUID = Field(foreign_key="darajaintegration.id", index=True)
    client_reference: str = Field(max_length=100)
    amount_minor: int = Field(gt=0)
    currency: str = Field(default="KES", min_length=3, max_length=3)
    phone_number: str | None = Field(default=None, max_length=20, nullable=True)
    payment_source: str = Field(default="stk", max_length=16, index=True)
    direction: str = Field(default="inbound", max_length=16)
    description: str | None = Field(default=None, max_length=250)
    status: str = Field(default="pending", max_length=24, index=True)
    provider_checkout_request_id: str | None = Field(default=None, max_length=120, index=True)
    provider_merchant_request_id: str | None = Field(default=None, max_length=120, index=True)
    provider_receipt: str | None = Field(default=None, max_length=64, index=True)
    provider_result_code: str | None = Field(default=None, max_length=32)
    provider_result_description: str | None = Field(default=None, max_length=250)
    initiated_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    succeeded_at: datetime | None = Field(default=None)
    failed_at: datetime | None = Field(default=None)
    cancelled_at: datetime | None = Field(default=None)


class IdempotencyRecord(BaseMixin, table=True):
    """Stable request identity preventing duplicate merchant operations."""

    __table_args__ = (UniqueConstraint("merchant_id", "key", name="uq_idempotency_merchant_key"),)

    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    # Optional during compatibility rollout; new callers should bind the client.
    client_id: UUID | None = Field(default=None, foreign_key="m2mclient.id", index=True)
    key: str = Field(max_length=200)
    request_hash: str = Field(max_length=64)
    resource_id: UUID | None = Field(default=None, index=True)
    response_status: int | None = Field(default=None)
    response_snapshot: dict[str, object] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    expires_at: datetime | None = Field(default=None, index=True)


class ProviderCallback(BaseMixin, table=True):
    """Durable, deduplicated evidence received from a provider callback."""

    __table_args__ = (
        UniqueConstraint("integration_id", "dedupe_fingerprint", name="uq_callback_integration_fingerprint"),
    )

    integration_id: UUID = Field(foreign_key="darajaintegration.id", index=True)
    merchant_id: UUID | None = Field(default=None, foreign_key="merchant.id", index=True)
    payment_id: UUID | None = Field(default=None, foreign_key="payment.id", index=True)
    callback_type: str = Field(max_length=32, index=True)
    dedupe_fingerprint: str = Field(max_length=64)
    provider_event_id: str | None = Field(default=None, max_length=120)
    provider_transaction_id: str | None = Field(default=None, max_length=120, index=True)
    safe_payload: dict[str, object] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    processing_status: str = Field(default="received", max_length=24, index=True)
    processing_error: str | None = Field(default=None, max_length=500)
    received_at: datetime = Field(default_factory=utc_now, nullable=False)
    processed_at: datetime | None = Field(default=None)
