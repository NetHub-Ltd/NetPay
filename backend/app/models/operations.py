"""Provider request, verification, reconciliation, delivery, and audit records."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, JSON, LargeBinary, CheckConstraint, UniqueConstraint
from sqlmodel import Field

from app.models.base import BaseMixin, utc_now


class ProviderRequest(BaseMixin, table=True):
    """One outbound provider operation and its safe request/response evidence."""

    __tablename__ = "providerrequest"

    merchant_id: UUID | None = Field(default=None, foreign_key="merchant.id", index=True)
    integration_id: UUID = Field(foreign_key="providerintegration.id", index=True)
    payment_id: UUID | None = Field(default=None, foreign_key="payment.id", index=True)
    payment_attempt_id: UUID | None = Field(default=None, foreign_key="paymentattempt.id", index=True)
    operation: str = Field(max_length=48, index=True)
    correlation_id: UUID = Field(default_factory=uuid4, unique=True, index=True)
    provider_request_id: str | None = Field(default=None, max_length=120, index=True)
    http_status: int | None = Field(default=None)
    outcome: str = Field(default="started", max_length=32, index=True)
    request_metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    response_metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    started_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True), nullable=False)
    completed_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))


class PaymentVerification(BaseMixin, table=True):
    """Historical result of checking a payment against provider-authoritative evidence."""

    __tablename__ = "paymentverification"

    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    payment_id: UUID = Field(foreign_key="payment.id", index=True)
    payment_attempt_id: UUID | None = Field(default=None, foreign_key="paymentattempt.id", index=True)
    provider_request_id: UUID | None = Field(default=None, foreign_key="providerrequest.id", index=True)
    status: str = Field(default="requested", max_length=32, index=True)
    provider_transaction_id: str | None = Field(default=None, max_length=120, index=True)
    checked_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True), nullable=False)
    evidence: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    error_code: str | None = Field(default=None, max_length=100)
    error_message: str | None = Field(default=None, max_length=500)


class ReconciliationRun(BaseMixin, table=True):
    """One bounded comparison between NetPay records and provider evidence."""

    __tablename__ = "reconciliationrun"
    __table_args__ = (CheckConstraint("window_start < window_end", name="ck_reconciliation_window_order"),)

    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    integration_id: UUID = Field(foreign_key="providerintegration.id", index=True)
    source: str = Field(max_length=48)
    window_start: datetime = Field(sa_type=DateTime(timezone=True), nullable=False)
    window_end: datetime = Field(sa_type=DateTime(timezone=True), nullable=False)
    status: str = Field(default="pending", max_length=32, index=True)
    started_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    completed_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    summary: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    error_summary: str | None = Field(default=None, max_length=500)


class ReconciliationItem(BaseMixin, table=True):
    """Preserve one match decision or discrepancy from a reconciliation run."""

    __tablename__ = "reconciliationitem"
    __table_args__ = (
        UniqueConstraint("reconciliation_run_id", "provider_transaction_id", name="uq_reconciliation_item_provider_transaction"),
        CheckConstraint("provider_amount_minor IS NULL OR provider_amount_minor >= 0", name="ck_reconciliation_provider_amount_nonnegative"),
        CheckConstraint("netpay_amount_minor IS NULL OR netpay_amount_minor >= 0", name="ck_reconciliation_netpay_amount_nonnegative"),
    )

    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    reconciliation_run_id: UUID = Field(foreign_key="reconciliationrun.id", index=True)
    payment_id: UUID | None = Field(default=None, foreign_key="payment.id", index=True)
    provider_transaction_id: str | None = Field(default=None, max_length=120, index=True)
    match_status: str = Field(max_length=40, index=True)
    provider_amount_minor: int | None = Field(default=None, ge=0)
    netpay_amount_minor: int | None = Field(default=None, ge=0)
    currency: str = Field(default="KES", min_length=3, max_length=3)
    provider_status: str | None = Field(default=None, max_length=48)
    netpay_status: str | None = Field(default=None, max_length=48)
    details: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    resolved_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    resolution_note: str | None = Field(default=None, max_length=500)


class WebhookEndpoint(BaseMixin, table=True):
    """A merchant-owned HTTPS destination subscribed to selected event types."""

    __tablename__ = "webhookendpoint"

    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    url: str = Field(max_length=512)
    status: str = Field(default="active", max_length=24, index=True)
    subscribed_events: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    signing_secret_ciphertext: bytes | None = Field(default=None, sa_column=Column("signing_secret_ciphertext", LargeBinary, nullable=True))
    signing_secret_reference: str | None = Field(default=None, max_length=255)
    last_success_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))


class EventDelivery(BaseMixin, table=True):
    """Current delivery state for one outbox event and one webhook endpoint."""

    __tablename__ = "eventdelivery"
    __table_args__ = (UniqueConstraint("outbox_event_id", "webhook_endpoint_id", name="uq_event_delivery_event_endpoint"),)

    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    outbox_event_id: UUID = Field(foreign_key="eventoutbox.id", index=True)
    webhook_endpoint_id: UUID = Field(foreign_key="webhookendpoint.id", index=True)
    status: str = Field(default="pending", max_length=32, index=True)
    attempt_count: int = Field(default=0, ge=0)
    next_attempt_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True), index=True, nullable=False)
    last_http_status: int | None = Field(default=None)
    last_error: str | None = Field(default=None, max_length=500)
    delivered_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))


class AuditLog(BaseMixin, table=True):
    """Append-only audit evidence for security-sensitive configuration changes."""

    __tablename__ = "auditevent"

    merchant_id: UUID | None = Field(default=None, foreign_key="merchant.id", index=True)
    actor_type: str = Field(max_length=32)
    actor_id: UUID | None = Field(default=None)
    action: str = Field(max_length=100, index=True)
    resource_type: str = Field(max_length=80)
    resource_id: UUID | None = Field(default=None, index=True)
    occurred_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True), index=True, nullable=False)
    metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
