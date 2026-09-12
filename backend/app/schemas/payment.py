from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class IntentCreate(BaseModel):
    integration_public_id: str
    phone: str
    amount_minor: int = Field(gt=0, description="Amount in minor units (100 = 1.00 KES)")
    account_reference: Optional[str] = Field(default="PAY", max_length=12)
    description: Optional[str] = Field(default="Payment", max_length=32)
    context: Optional[dict[str, Any]] = None
    # Optional legacy major-unit amount; converted to amount_minor if amount_minor omitted in older clients
    amount: Optional[Decimal] = Field(default=None, gt=0)

    @model_validator(mode="before")
    @classmethod
    def coerce_legacy_amount(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if data.get("amount_minor") is None and data.get("amount") is not None:
            major = Decimal(str(data["amount"]))
            data["amount_minor"] = int(major * 100)
        return data


class IntentCreateResponse(BaseModel):
    id: UUID
    status: str
    amount_minor: int
    
    provider_checkout_id: Optional[str] = None
    provider_merchant_id: Optional[str] = None
    message: str = "STK push initiated"
    idempotent_replay: bool = False


class IntentOut(BaseModel):
    id: UUID
    tenant_id: UUID
    integration_id: UUID
    status: str
    amount_minor: int
    amount: Decimal
    currency: str
    phone: str
    account_reference: Optional[str] = None
    description: Optional[str] = None
    provider_checkout_id: Optional[str] = None
    provider_merchant_id: Optional[str] = None
    provider_transaction_id: Optional[str] = None
    failure_reason: Optional[str] = None
    idempotency_key: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
