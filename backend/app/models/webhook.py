from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlmodel import Field
from app.models.base import BaseMixin

class Webhook(BaseMixin, table=True):
    __tablename__ = "webhooks"
    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    url: str = Field(max_length=512)
    secret: str = Field(max_length=128)
    last_live_at: Optional[datetime] = Field(default=None)

class WebhookDelivery(BaseMixin, table=True):
    __tablename__ = "webhook_deliveries"
    webhook_id: UUID = Field(foreign_key="webhooks.id", index=True)
    payment_intent_id: Optional[UUID] = Field(default=None, index=True)
    status_code: Optional[int] = Field(default=None)
    ok: bool = Field(default=False)
    error: Optional[str] = Field(default=None, max_length=512)
