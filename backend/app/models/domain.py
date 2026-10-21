"""Fresh payment persistence schema with UTC timestamps and integer minor units."""
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4
from sqlalchemy import CheckConstraint, Column, DateTime, Integer, JSON, LargeBinary, String, UniqueConstraint
from sqlmodel import Field, SQLModel

def utc_now() -> datetime:
    """Return an aware UTC timestamp."""
    return datetime.now(UTC)

class Record(SQLModel):
    """Common UUID identity and timezone-aware lifecycle timestamps."""
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True))
    updated_at: datetime = Field(default_factory=utc_now, sa_type=DateTime(timezone=True), sa_column_kwargs={"onupdate": utc_now})
    deleted_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))

class Merchant(Record, table=True):
    __tablename__ = "merchant"
    __table_args__ = (UniqueConstraint("slug", name="uq_merchant_slug"),)
    name: str = Field(sa_column=Column(String(160), nullable=False))
    slug: str = Field(sa_column=Column(String(100), nullable=False, index=True))
    default_currency: str = Field(default="KES", sa_column=Column(String(3), nullable=False))
    status: str = Field(default="active", sa_column=Column(String(24), nullable=False))

class ProviderIntegration(Record, table=True):
    __tablename__ = "providerintegration"
    __table_args__ = (UniqueConstraint("merchant_id", "provider", "environment", name="uq_integration_provider_environment"),)
    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    provider: str = Field(sa_column=Column(String(32), nullable=False))
    environment: str = Field(default="sandbox", sa_column=Column(String(16), nullable=False))
    status: str = Field(default="pending", sa_column=Column(String(24), nullable=False))
    credentials_ciphertext: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True))
    credential_reference: str | None = Field(default=None, sa_column=Column(String(255), nullable=True))

class Payment(Record, table=True):
    __tablename__ = "payment"
    __table_args__ = (UniqueConstraint("merchant_id", "merchant_reference", name="uq_payment_merchant_reference"), CheckConstraint("amount_minor > 0", name="ck_payment_amount_positive"))
    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    integration_id: UUID = Field(foreign_key="providerintegration.id", index=True)
    direction: str = Field(default="inbound", sa_column=Column(String(16), nullable=False))
    merchant_reference: str = Field(sa_column=Column(String(120), nullable=False))
    provider_transaction_id: str | None = Field(default=None, sa_column=Column(String(120), nullable=True, index=True))
    amount_minor: int = Field(sa_column=Column(Integer, nullable=False))
    currency: str = Field(default="KES", sa_column=Column(String(3), nullable=False))
    status: str = Field(default="pending", sa_column=Column(String(32), nullable=False, index=True))
    description: str | None = Field(default=None, sa_column=Column(String(250), nullable=True))
    succeeded_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    failed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))

class PaymentAttempt(Record, table=True):
    __tablename__ = "paymentattempt"
    __table_args__ = (UniqueConstraint("payment_id", "attempt_number", name="uq_payment_attempt_number"),)
    payment_id: UUID = Field(foreign_key="payment.id", index=True)
    attempt_number: int = Field(sa_column=Column(Integer, nullable=False))
    status: str = Field(default="started", sa_column=Column(String(32), nullable=False))
    started_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))
    completed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    error_code: str | None = Field(default=None, sa_column=Column(String(100), nullable=True))
    error_message: str | None = Field(default=None, sa_column=Column(String(500), nullable=True))

class IdempotencyRecord(Record, table=True):
    __tablename__ = "idempotencyrecord"
    __table_args__ = (UniqueConstraint("merchant_id", "key", name="uq_idempotency_merchant_key"),)
    merchant_id: UUID = Field(foreign_key="merchant.id", index=True)
    key: str = Field(sa_column=Column(String(160), nullable=False))
    request_hash: str = Field(sa_column=Column(String(64), nullable=False))
    response_status: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    response_snapshot: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    expires_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))

class ProviderCallback(Record, table=True):
    __tablename__ = "providercallback"
    __table_args__ = (UniqueConstraint("integration_id", "provider_event_id", name="uq_callback_integration_event"),)
    integration_id: UUID = Field(foreign_key="providerintegration.id", index=True)
    provider_event_id: str = Field(sa_column=Column(String(120), nullable=False))
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    received_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))
    processing_status: str = Field(default="received", sa_column=Column(String(24), nullable=False, index=True))
    processed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))

class OutboxEvent(Record, table=True):
    __tablename__ = "eventoutbox"
    event_type: str = Field(sa_column=Column(String(100), nullable=False, index=True))
    aggregate_type: str = Field(sa_column=Column(String(50), nullable=False))
    aggregate_id: UUID = Field(index=True)
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    occurred_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))
    published_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True, index=True))
    attempt_count: int = Field(default=0, sa_column=Column(Integer, nullable=False))

class AuditEvent(Record, table=True):
    __tablename__ = "auditevent"
    merchant_id: UUID | None = Field(default=None, foreign_key="merchant.id", index=True)
    actor_type: str = Field(sa_column=Column(String(32), nullable=False))
    actor_id: UUID | None = Field(default=None)
    action: str = Field(sa_column=Column(String(100), nullable=False, index=True))
    resource_type: str = Field(sa_column=Column(String(80), nullable=False))
    resource_id: UUID | None = Field(default=None, index=True)
    metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
