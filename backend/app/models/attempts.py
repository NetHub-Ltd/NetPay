"""Payment attempt history and safe provider outcome metadata."""

from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from app.models.base import BaseMixin


class PaymentAttempt(BaseMixin, table=True):
    """One attempt associated with a canonical payment."""

    __tablename__ = "paymentattempt"
    __table_args__ = (UniqueConstraint("payment_id", "attempt_number", name="uq_payment_attempt_number"),)

    payment_id: UUID = Field(foreign_key="payment.id", index=True)
    attempt_number: int = Field(ge=1)
    correlation_id: UUID = Field(default_factory=uuid4, unique=True, index=True)
    status: str = Field(default="started", max_length=32, index=True)
    provider_result_code: str | None = Field(default=None, max_length=32)
    error_code: str | None = Field(default=None, max_length=100)
    error_message: str | None = Field(default=None, max_length=500)
    safe_error_code: str | None = Field(default=None, max_length=100)
    safe_error_message: str | None = Field(default=None, max_length=500)
