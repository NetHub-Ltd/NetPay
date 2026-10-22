"""Typed request and result contracts for supported Daraja operations."""
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class APIModel(BaseModel):
    """Base provider contract: typed fields and no silent extra payload keys."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("amount_minor", check_fields=False)
    @classmethod
    def require_whole_kes_shillings(cls, value: int) -> int:
        """Daraja amount fields accept whole KES shillings, not fractional minor units."""
        if value <= 0 or value % 100:
            raise ValueError("amount_minor must represent a positive whole KES shilling amount")
        return value


class OperationOutcome(StrEnum):
    """Transport/provider outcome; accepted is not the same as paid."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    UNKNOWN = "unknown"
    NOT_SENT = "not_sent"


class OperationResult(BaseModel):
    """Safe normalized result returned by an internal Core operation."""

    operation: str
    outcome: OperationOutcome
    correlation_id: UUID
    http_status: int | None = None
    provider_request_id: str | None = None
    provider_code: str | None = None
    provider_description: str | None = None
    data: dict[str, object] = Field(default_factory=dict)


class STKPushRequest(APIModel):
    """Request a customer authorization prompt for an integer KES amount."""

    phone_number: str = Field(min_length=9, max_length=16)
    amount_minor: int = Field(gt=0)
    account_reference: str = Field(min_length=1, max_length=12)
    description: str = Field(min_length=1, max_length=13)
    currency: Literal["KES"] = "KES"


class STKQueryRequest(APIModel):
    """Query the current provider result for a known checkout request."""

    checkout_request_id: str = Field(min_length=1, max_length=120)


class C2BRegistrationRequest(APIModel):
    """Register generated NetPay URLs for a merchant that opted into C2B."""

    response_type: Literal["Completed", "Cancelled"] = "Completed"


class DynamicQRRequest(APIModel):
    """Generate a Dynamic QR code for a supported transaction type."""

    merchant_name: str = Field(min_length=1, max_length=100)
    reference: str = Field(min_length=1, max_length=100)
    amount_minor: int = Field(gt=0)
    transaction_code: Literal["BG", "PB", "WA", "SM", "SB"]
    credit_party_identifier: str = Field(min_length=1, max_length=32)
    size: int = Field(default=300, ge=100, le=1000)
    currency: Literal["KES"] = "KES"


class TransactionStatusRequest(APIModel):
    """Query status by receipt or originating conversation identifier."""

    transaction_id: str | None = Field(default=None, max_length=120)
    original_conversation_id: str | None = Field(default=None, max_length=120)
    party_a: str | None = Field(default=None, max_length=32)
    identifier_type: Literal["1", "2", "4"] = "4"
    remarks: str = Field(default="NetPay status check", max_length=100)
    occasion: str = Field(default="", max_length=100)

    @model_validator(mode="after")
    def require_transaction_reference(self) -> "TransactionStatusRequest":
        """A status query must identify a known transaction or request."""
        if not self.transaction_id and not self.original_conversation_id:
            raise ValueError("transaction_id or original_conversation_id is required")
        return self


class AccountBalanceRequest(APIModel):
    """Request an asynchronous balance query for a permitted organization."""

    identifier_type: Literal["1", "2", "4"] = "4"
    remarks: str = Field(default="NetPay balance query", max_length=100)
    occasion: str = Field(default="", max_length=100)


class ReversalRequest(APIModel):
    """Request a reversal only when separately authorized by the application."""

    transaction_id: str = Field(min_length=1, max_length=120)
    amount_minor: int = Field(gt=0)
    receiver_party: str = Field(min_length=1, max_length=32)
    receiver_identifier_type: Literal["1", "2", "4"] = "4"
    remarks: str = Field(min_length=1, max_length=100)
    occasion: str = Field(default="", max_length=100)
    currency: Literal["KES"] = "KES"


class B2CPaymentRequest(APIModel):
    """Request a disbursement; application authorization and limits are mandatory."""

    phone_number: str = Field(min_length=9, max_length=16)
    amount_minor: int = Field(gt=0)
    command_id: Literal["BusinessPayment", "SalaryPayment", "PromotionPayment"] = "BusinessPayment"
    remarks: str = Field(min_length=1, max_length=100)
    occasion: str = Field(default="", max_length=100)
    currency: Literal["KES"] = "KES"


class B2BPaymentRequest(APIModel):
    """Request an explicitly permitted business-to-business operation."""

    party_b: str = Field(min_length=1, max_length=32)
    amount_minor: int = Field(gt=0)
    command_id: Literal[
        "BusinessPayBill",
        "BusinessBuyGoods",
        "BusinessTransfer",
        "BusinessTransferFromMMFToUtility",
    ]
    sender_identifier_type: Literal["1", "2", "4"] = "4"
    receiver_identifier_type: Literal["1", "2", "4"] = "4"
    account_reference: str = Field(default="", max_length=100)
    remarks: str = Field(min_length=1, max_length=100)
    occasion: str = Field(default="", max_length=100)
    currency: Literal["KES"] = "KES"


class PullTransactionsRequest(APIModel):
    """Retrieve a bounded transaction window when the product is enabled."""

    start_date: datetime
    end_date: datetime
    offset: int = Field(default=0, ge=0)
    account_number: str = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def require_ordered_window(self) -> "PullTransactionsRequest":
        """Require aware timestamps and a strictly increasing bounded window."""
        if self.start_date.tzinfo is None or self.end_date.tzinfo is None:
            raise ValueError("start_date and end_date must be timezone-aware")
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        if (self.end_date - self.start_date).days > 31:
            raise ValueError("transaction window cannot exceed 31 days")
        return self


class CallbackReceipt(BaseModel):
    """Processing summary for a durable, deduplicated provider callback."""

    status: Literal["recorded", "duplicate", "conflict"]
    integration_id: str
    callback_type: str
    validation_accepted: bool | None = None


class STKCallbackEvidence(BaseModel):
    """Normalized, minimized STK callback evidence."""

    merchant_request_id: str
    checkout_request_id: str
    result_code: int
    result_description: str = ""
    amount: Decimal | None = None
    receipt_number: str | None = None
    transaction_date: str | None = None
    phone_number: str | None = None
    fingerprint: str
