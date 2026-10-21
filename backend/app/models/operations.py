"""Verification, provider request, reconciliation, endpoint, and audit tables.

These records preserve evidence and retry history separately from canonical
payment state. Provider-specific payloads are bounded, sanitized JSON rather
than a substitute for typed fields used in matching and integrity constraints.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, CheckConstraint, UniqueConstraint
from sqlmodel import Field

from app.models.base import BaseMixin, utc_now


class ProviderRequest(BaseMixin, table=True):
    """One outbound provider operation and its safe request/response evidence."""

    merchant_id: UUID | None = Field(default=None, foreign_key="merchant.id", index=True)
    integration_id: UUID = Field(foreign_key="darajaintegration.id", index=True)
    payment_id: UUID | None = Field(default=None, foreign_key="payment.id", index=True)
    payment_attempt_id: UUID | None = Field(default=None, foreign_key="paymentattempt.id", index=True)
    operation: str = Field(max_length=48, index=True)
    correlation_id: UUID = Field(default_factory=uuid4, unique=True, index=True)
    provider_request_id: str | None = Field(default=None, max_length=120, index=True)
    http_status: int | None = Field(default=None)
    outcome: str = Field(default="started", max_length=32, index=True)
    request_metadata: dict[str, object] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    response_metadata: dict[str, object] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    started_at: datetime = Field(default_factory=utc_now, nullable=False)
    completed_at: datetime | None = Field(default=None)


class PaymentVerification(BaseMixin, table=True):
    """Historical result of checking a payment with provider-authoritative evidence."""

    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    payment_id: UUID = Field(foreign_key="payment.id", index=True)
    payment_attempt_id: UUID | None = Field(default=None, foreign_key="paymentattempt.id", index=True)
    provider_request_id: UUID | None = Field(default=None, foreign_key="providerrequest.id", index=True)
    status: str = Field(default="requested", max_length=32, index=True)
    provider_transaction_id: str | None = Field(default=None, max_length=120, index=True)
    checked_at: datetime = Field(default_factory=utc_now, nullable=False)
    evidence: dict[str, object] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    error_code: str | None = Field(default=None, max_length=100)
    error_message: str | None = Field(default=None, max_length=500)


class ReconciliationRun(BaseMixin, table=True):
    """One bounded comparison between NetPay records and provider evidence."""

    __table_args__ = (
        CheckConstraint("window_start < window_end", name="ck_reconciliation_window_order"),
    )

    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    integration_id: UUID = Field(foreign_key="darajaintegration.id", index=True)
    source: str = Field(max_length=48)
    window_start: datetime = Field(nullable=False)
    window_end: datetime = Field(nullable=False)
    status: str = Field(default="pending", max_length=32, index=True)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    summary: dict[str, object] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    error_summary: str | None = Field(default=None, max_length=500)


class ReconciliationItem(BaseMixin, table=True):
    """Preserve one match decision or discrepancy from a reconciliation run."""

    __table_args__ = (
        UniqueConstraint(
            "reconciliation_run_id", "provider_transaction_id",
            name="uq_reconciliation_item_provider_transaction",
        ),
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
    details: dict[str, object] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    resolved_at: datetime | None = Field(default=None)
    resolution_note: str | None = Field(default=None, max_length=500)


class WebhookEndpoint(BaseMixin, table=True):
    """A merchant-owned HTTPS destination subscribed to selected event types."""

    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    url: str = Field(max_length=512)
    status: str = Field(default="active", max_length=24, index=True)
    subscribed_events: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    # Ciphertext or secret-manager reference only; never serialize this field to APIs.
    signing_secret_ciphertext: bytes | None = Field(default=None)
    signing_secret_reference: str | None = Field(default=None, max_length=255)
    last_success_at: datetime | None = Field(default=None)


class EventDelivery(BaseMixin, table=True):
    """Current delivery state for one outbox event and one webhook endpoint."""

    __table_args__ = (
        UniqueConstraint("outbox_event_id", "webhook_endpoint_id", name="uq_event_delivery_event_endpoint"),
    )

    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    outbox_event_id: UUID = Field(foreign_key="eventoutbox.id", index=True)
    webhook_endpoint_id: UUID = Field(foreign_key="webhookendpoint.id", index=True)
    status: str = Field(default="pending", max_length=32, index=True)
    attempt_count: int = Field(default=0, ge=0, nullable=False)
    next_attempt_at: datetime = Field(default_factory=utc_now, index=True, nullable=False)
    last_http_status: int | None = Field(default=None)
    last_error: str | None = Field(default=None, max_length=500)
    delivered_at: datetime | None = Field(default=None)


class AuditLog(BaseMixin, table=True):
    """Append-only audit evidence for security-sensitive configuration changes."""

    merchant_id: UUID | None = Field(default=None, foreign_key="merchant.id", index=True)
    actor_type: str = Field(max_length=32)
    actor_id: str | None = Field(default=None, max_length=120)
    action: str = Field(max_length=100, index=True)
    target_type: str = Field(max_length=100)
    target_id: str | None = Field(default=None, max_length=120, index=True)
    occurred_at: datetime = Field(default_factory=utc_now, index=True, nullable=False)
    metadata_json: dict[str, object] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
