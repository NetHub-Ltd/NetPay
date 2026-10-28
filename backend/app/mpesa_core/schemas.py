"""Typed requests and results for supported Daraja operations."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator

from app.mpesa_core.errors import OperationOutcome, RetryDisposition


Environment = Literal["sandbox", "production"]


class CoreModel(BaseModel):
    """Base schema that hides invalid input values in validation errors."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class DarajaCredentials(CoreModel):
    """Resolved credentials supplied by NetPay; Core never persists them."""

    consumer_key: SecretStr
    consumer_secret: SecretStr
    passkey: SecretStr | None = None
    initiator_name: str | None = None
    initiator_password: SecretStr | None = None
    security_credential: SecretStr | None = None
    credential_version: int = Field(default=1, ge=1)


class IntegrationContext(CoreModel):
    """Non-persistent integration context resolved by the application."""

    integration_id: str = Field(min_length=1, max_length=64)
    environment: Environment
    shortcode: str = Field(min_length=1, max_length=32)
    product_type: str | None = Field(default=None, max_length=24)
    party_b_shortcode: str | None = Field(default=None, max_length=32)
    enabled_capabilities: frozenset[str] = frozenset({"stk_push"})
    credentials: DarajaCredentials

    @field_validator("shortcode", "party_b_shortcode")
    @classmethod
    def validate_shortcode(cls, value: str | None) -> str | None:
        if value is not None and not value.isdigit():
            raise ValueError("shortcode must contain digits only")
        return value


class ProviderOperationResult(CoreModel):
    """Normalized operation response; never represents payment success implicitly."""

    operation: str
    outcome: OperationOutcome
    response: dict[str, Any] = Field(default_factory=dict)
    provider_request_id: str | None = None
    conversation_id: str | None = None
    originator_conversation_id: str | None = None
    http_status: int | None = None
    retry_disposition: RetryDisposition = RetryDisposition.NEVER


class STKPushRequest(CoreModel):
    """STK request; amount_minor uses 100 units per KES."""

    phone_number: str
    amount_minor: int = Field(gt=0)
    account_reference: str = Field(min_length=1, max_length=12)
    description: str = Field(min_length=1, max_length=13)
    callback_url: str | None = None
    transaction_type: Literal["CustomerPayBillOnline", "CustomerBuyGoodsOnline"] = "CustomerPayBillOnline"

    @field_validator("amount_minor")
    @classmethod
    def whole_shillings(cls, value: int) -> int:
        if value % 100:
            raise ValueError("STK amount must be a whole KES shilling amount")
        return value


class STKQueryRequest(CoreModel):
    checkout_request_id: str = Field(min_length=1, max_length=128)


class C2BRegistrationRequest(CoreModel):
    validation_url: str
    confirmation_url: str
    response_type: Literal["Completed", "Cancelled"] = "Completed"


class C2BSimulationRequest(CoreModel):
    phone_number: str
    amount_minor: int = Field(gt=0)
    bill_reference: str = Field(min_length=1, max_length=20)

    @field_validator("amount_minor")
    @classmethod
    def whole_shillings(cls, value: int) -> int:
        if value % 100:
            raise ValueError("C2B amount must be whole KES shillings")
        return value


class DynamicQRRequest(CoreModel):
    merchant_name: str = Field(min_length=1, max_length=64)
    reference: str = Field(min_length=1, max_length=20)
    amount_minor: int = Field(gt=0)
    transaction_code: Literal["BG", "WA", "PB", "SM", "SB"]
    credit_party_identifier: str = Field(min_length=1, max_length=32)
    size: int = Field(default=300, ge=100, le=1000)

    @field_validator("amount_minor")
    @classmethod
    def whole_shillings(cls, value: int) -> int:
        if value % 100:
            raise ValueError("QR amount must be whole KES shillings")
        return value


class TransactionStatusRequest(CoreModel):
    transaction_id: str | None = Field(default=None, max_length=32)
    original_conversation_id: str | None = Field(default=None, max_length=128)
    result_url: str
    timeout_url: str
    remarks: str = Field(default="Status query", max_length=100)
    occasion: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def one_identifier(self) -> "TransactionStatusRequest":
        if not self.transaction_id and not self.original_conversation_id:
            raise ValueError("transaction_id or original_conversation_id is required")
        return self


class AccountBalanceRequest(CoreModel):
    result_url: str
    timeout_url: str
    remarks: str = Field(default="Account balance query", max_length=100)


class ReversalRequest(CoreModel):
    transaction_id: str = Field(min_length=1, max_length=32)
    amount_minor: int = Field(gt=0)
    receiver_party: str = Field(min_length=1, max_length=32)
    result_url: str
    timeout_url: str
    remarks: str = Field(default="Transaction reversal", max_length=100)
    occasion: str | None = Field(default=None, max_length=100)

    @field_validator("amount_minor")
    @classmethod
    def whole_shillings(cls, value: int) -> int:
        if value % 100:
            raise ValueError("reversal amount must be whole KES shillings")
        return value


class B2CPaymentRequest(CoreModel):
    phone_number: str
    amount_minor: int = Field(gt=0)
    originator_conversation_id: str = Field(min_length=1, max_length=20)
    result_url: str
    timeout_url: str
    command_id: Literal["BusinessPayment", "SalaryPayment", "PromotionPayment"] = "BusinessPayment"
    remarks: str = Field(default="Business payment", max_length=100)
    occasion: str | None = Field(default=None, max_length=100)

    @field_validator("amount_minor")
    @classmethod
    def whole_shillings(cls, value: int) -> int:
        if value % 100:
            raise ValueError("B2C amount must be whole KES shillings")
        return value


class B2BPaymentRequest(CoreModel):
    party_b: str = Field(min_length=1, max_length=32)
    amount_minor: int = Field(gt=0)
    command_id: Literal[
        "BusinessPayBill", "BusinessBuyGoods", "BusinessToBusinessTransfer",
        "BusinessTransferFromMMFToUtility", "BusinessTransferFromUtilityToMMF",
    ]
    result_url: str
    timeout_url: str
    account_reference: str | None = Field(default=None, max_length=20)
    remarks: str = Field(default="Business transfer", max_length=100)
    occasion: str | None = Field(default=None, max_length=100)

    @field_validator("amount_minor")
    @classmethod
    def whole_shillings(cls, value: int) -> int:
        if value % 100:
            raise ValueError("B2B amount must be whole KES shillings")
        return value


class TaxRemittanceRequest(CoreModel):
    """KRA tax remittance using the documented B2B remittax product."""

    prn: str = Field(min_length=1, max_length=32)
    amount_minor: int = Field(gt=0)
    result_url: str
    timeout_url: str
    remarks: str = Field(default="Tax remittance", max_length=100)

    @field_validator("amount_minor")
    @classmethod
    def whole_shillings(cls, value: int) -> int:
        if value % 100:
            raise ValueError("tax remittance amount must be whole KES shillings")
        return value


class PullTransactionsRequest(CoreModel):
    """Reserved for the documented Pull Transactions contract once confirmed."""

    start_at: datetime
    end_at: datetime
    response_url: str | None = None

    @model_validator(mode="after")
    def ordered_window(self) -> "PullTransactionsRequest":
        if self.start_at.tzinfo is None or self.end_at.tzinfo is None:
            raise ValueError("start_at and end_at must be timezone-aware")
        if self.start_at >= self.end_at:
            raise ValueError("start_at must be earlier than end_at")
        return self


class STKCallback(CoreModel):
    """Validated STK callback fields, with optional provider metadata."""

    merchant_request_id: str = Field(alias="MerchantRequestID")
    checkout_request_id: str = Field(alias="CheckoutRequestID")
    result_code: int = Field(alias="ResultCode")
    result_description: str = Field(alias="ResultDesc")
    callback_metadata: dict[str, Any] | None = Field(default=None, alias="CallbackMetadata")


class C2BCallback(CoreModel):
    """Normalized C2B confirmation/validation payload."""

    transaction_type: str | None = Field(default=None, alias="TransactionType")
    trans_id: str = Field(alias="TransID")
    trans_time: str = Field(alias="TransTime")
    trans_amount: str = Field(alias="TransAmount")
    business_short_code: str = Field(alias="BusinessShortCode")
    bill_ref_number: str | None = Field(default=None, alias="BillRefNumber")
    msisdn: str | None = Field(default=None, alias="MSISDN")
    invoice_number: str | None = Field(default=None, alias="InvoiceNumber")


class AsyncResultCallback(CoreModel):
    """Common envelope for asynchronous Daraja result callbacks."""

    result: dict[str, Any] = Field(alias="Result")


class CatalogueOperationRequest(CoreModel):
    """Typed envelope for a product whose current portal schema is not public here."""

    operation: Literal["bill_manager", "ratiba", "lipa_na_bonga", "b2b_express_checkout"]
    payload: dict[str, Any] = Field(default_factory=dict)
