"""Typed API contracts; provider credentials are never response fields."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class IntegrationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    environment: Literal["sandbox", "production"] = "sandbox"
    shortcode: str = Field(min_length=5, max_length=32, pattern=r"^[0-9]+$")
    product_type: Literal["paybill", "till"]
    consumer_key: SecretStr = Field(min_length=1)
    consumer_secret: SecretStr = Field(min_length=1)
    passkey: SecretStr = Field(min_length=1)


class IntegrationSummary(BaseModel):
    id: UUID
    integration_id: str
    environment: str
    shortcode: str
    product_type: str
    credential_status: str
    c2b_enabled: bool
    c2b_registration_status: str
    stk_callback_url: str
    c2b_validation_url: str
    c2b_confirmation_url: str
    created_at: datetime


class IntegrationList(BaseModel):
    items: list[IntegrationSummary]


class ErrorResponse(BaseModel):
    code: str
    message: str


class PaymentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    integration_id: str = Field(min_length=16, max_length=64)
    client_reference: str = Field(min_length=1, max_length=100)
    amount_minor: int = Field(gt=0)
    currency: Literal["KES"] = "KES"
    phone_number: str = Field(min_length=10, max_length=16)
    description: str = Field(default="Payment", min_length=1, max_length=100)


class PaymentSummary(BaseModel):
    id: UUID
    client_reference: str
    amount_minor: int
    currency: str
    status: str
    provider_checkout_request_id: str | None
    created_at: datetime
    updated_at: datetime
