from __future__ import annotations
from typing import Optional
from uuid import UUID
from sqlmodel import Field
from app.models.base import BaseMixin

class GatewayEvent(BaseMixin, table=True):
    __tablename__ = "gateway_events"
    tenant_id: Optional[UUID] = Field(default=None, index=True)
    integration_id: Optional[UUID] = Field(default=None, index=True)
    payment_intent_id: Optional[UUID] = Field(default=None, index=True)
    category: str = Field(max_length=32)
    action: str = Field(max_length=64)
    message: str = Field(max_length=512)
    payload_json: Optional[str] = Field(default=None)
    is_replayable: bool = Field(default=False)
