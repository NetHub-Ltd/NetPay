from __future__ import annotations
from typing import Optional
from uuid import UUID
from sqlmodel import Field
from app.models.base import BaseMixin

class Integration(BaseMixin, table=True):
    __tablename__ = "integrations"
    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    public_id: str = Field(index=True, unique=True, max_length=32)
    shortcode: str = Field(max_length=12)
    type: str = Field(default="paybill", max_length=16)
    environment: str = Field(default="sandbox", max_length=16)
    status: str = Field(default="active", max_length=32)
    confirmation_url: Optional[str] = Field(default=None, max_length=512)
    validation_url: Optional[str] = Field(default=None, max_length=512)
    stk_callback_url: Optional[str] = Field(default=None, max_length=512)

class Credential(BaseMixin, table=True):
    __tablename__ = "credentials"
    integration_id: UUID = Field(foreign_key="integrations.id", index=True)
    kind: str = Field(max_length=32)  # consumer_key | consumer_secret | passkey
    value: str = Field(max_length=512)
