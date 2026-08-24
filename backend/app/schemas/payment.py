from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class IntentCreate(BaseModel):
    integration_public_id: str
    phone: str
    amount: Decimal = Field(gt=0)
    account_reference: Optional[str] = Field(default="PAY", max_length=12)
    description: Optional[str] = Field(default="Payment", max_length=32)
    context: Optional[dict[str, Any]] = None

class IntentCreateResponse(BaseModel):
    id: UUID
    status: str
    provider_checkout_id: Optional[str] = None
    provider_merchant_id: Optional[str] = None
    message: str = "STK push initiated"

class IntentOut(BaseModel):
    id: UUID
    tenant_id: UUID
    integration_id: UUID
    status: str
    amount: Decimal
    currency: str
    phone: str
    account_reference: Optional[str] = None
    description: Optional[str] = None
    provider_checkout_id: Optional[str] = None
    provider_merchant_id: Optional[str] = None
    provider_transaction_id: Optional[str] = None
    failure_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
