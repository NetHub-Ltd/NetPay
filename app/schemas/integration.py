from __future__ import annotations
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class IntegrationCreate(BaseModel):
    tenant_id: UUID
    shortcode: str = Field(max_length=12)
    type: Literal["paybill", "till"] = "paybill"
    environment: Literal["sandbox", "production"] = "sandbox"
    consumer_key: str
    consumer_secret: str
    passkey: str
    confirmation_url: Optional[str] = None
    validation_url: Optional[str] = None
    stk_callback_url: Optional[str] = None

class IntegrationOut(BaseModel):
    id: UUID
    public_id: str
    tenant_id: UUID
    shortcode: str
    type: str
    environment: str
    status: str
    confirmation_url: Optional[str] = None
    validation_url: Optional[str] = None
    stk_callback_url: Optional[str] = None
    model_config = {"from_attributes": True}

class RegisterUrlsRequest(BaseModel):
    confirmation_url: str
    validation_url: str
    response_type: Literal["Completed", "Cancelled"] = "Completed"
