"""Typed application-owned contracts for M2M and M-Pesa payment APIs."""
from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


class APIModel(BaseModel):
    """Hide rejected input values so credentials are not echoed in validation errors."""
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class TokenRequest(APIModel):
    grant_type: Literal["client_credentials"] = "client_credentials"
    client_id: str = Field(min_length=1, max_length=80)
    client_secret: SecretStr
    scope: str | None = Field(default=None, max_length=500)


class IntegrationCreate(APIModel):
    environment: Literal["sandbox", "production"] = "sandbox"
    shortcode: str = Field(min_length=1, max_length=32, pattern=r"^\d+$")
    product_type: Literal["paybill", "buygoods"] = "paybill"
    party_b_shortcode: str | None = Field(default=None, max_length=32, pattern=r"^\d+$")
    consumer_key: SecretStr
    consumer_secret: SecretStr
    passkey: SecretStr

    @field_validator("consumer_key", "consumer_secret", "passkey")
    @classmethod
    def nonempty_secret(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("credential values must not be empty")
        return value


class IntegrationEnableC2B(APIModel):
    enabled: bool


class STKInitiation(APIModel):
    integration_id: str = Field(min_length=1, max_length=64)
    phone_number: str = Field(min_length=9, max_length=16)
    amount_minor: int = Field(gt=0)
    merchant_reference: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=13)

    @field_validator("amount_minor")
    @classmethod
    def whole_kes_shillings(cls, value: int) -> int:
        if value % 100:
            raise ValueError("STK amount must be a whole KES shilling amount")
        return value


class PaymentView(APIModel):
    id: UUID
    merchant_reference: str
    amount_minor: int
    currency: str
    status: str
    provider_checkout_request_id: str | None = None
    provider_merchant_request_id: str | None = None
    provider_receipt: str | None = None
    provider_result_code: str | None = None
    created_at: str


class IntegrationView(APIModel):
    id: UUID
    integration_id: str
    environment: str
    shortcode: str
    product_type: str | None
    status: str
    credential_status: str
    enabled_capabilities: list[str]
    stk_callback_url: str
    c2b_validation_url: str
    c2b_confirmation_url: str
    c2b_enabled: bool
    c2b_registration_status: str
