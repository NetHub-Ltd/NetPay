from __future__ import annotations
from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlmodel import Field
from app.models.base import BaseMixin

class PaymentIntent(BaseMixin, table=True):
    __tablename__ = "payment_intents"
    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    integration_id: UUID = Field(foreign_key="integrations.id", index=True)
    created_by: Optional[UUID] = Field(default=None, index=True)
    intent_type: str = Field(default="collection", max_length=32)
    status: str = Field(default="created", index=True, max_length=32)
    amount: Decimal = Field(max_digits=18, decimal_places=2)
    currency: str = Field(default="KES", max_length=8)
    phone: str = Field(max_length=16)
    account_reference: Optional[str] = Field(default=None, max_length=12)
    description: Optional[str] = Field(default=None, max_length=32)
    context_json: Optional[str] = Field(default=None)
    provider: str = Field(default="mpesa", max_length=16)
    provider_checkout_id: Optional[str] = Field(default=None, index=True, max_length=64)
    provider_merchant_id: Optional[str] = Field(default=None, max_length=64)
    provider_transaction_id: Optional[str] = Field(default=None, index=True, max_length=64)
    failure_reason: Optional[str] = Field(default=None, max_length=512)
