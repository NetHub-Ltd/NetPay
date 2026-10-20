"""Provider initiation attempts for auditability without raw sensitive payloads."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PaymentAttempt(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("payment_id", "attempt_number", name="uq_payment_attempt_number"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    payment_id: UUID = Field(foreign_key="payment.id", index=True)
    attempt_number: int = Field(default=1, nullable=False)
    correlation_id: UUID = Field(default_factory=uuid4, unique=True, index=True)
    outcome: str = Field(default="created", max_length=24, index=True)
    provider_result_code: str | None = Field(default=None, max_length=32)
    safe_error_code: str | None = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)
