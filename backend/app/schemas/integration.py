from __future__ import annotations
from typing import Any, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field, model_validator


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
    connected: bool = False
    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def inject_connected(cls, data: Any) -> Any:
        if isinstance(data, dict):
            conf = data.get("confirmation_url")
            status = str(data.get("status") or "").lower()
            data = {**data, "connected": bool(conf) or status == "connected"}
            return data
        conf = getattr(data, "confirmation_url", None)
        status = str(getattr(data, "status", "") or "").lower()
        # Build dict from ORM-ish object for clean validation
        return {
            "id": getattr(data, "id"),
            "public_id": getattr(data, "public_id"),
            "tenant_id": getattr(data, "tenant_id"),
            "shortcode": getattr(data, "shortcode"),
            "type": getattr(data, "type"),
            "environment": getattr(data, "environment"),
            "status": getattr(data, "status"),
            "confirmation_url": conf,
            "validation_url": getattr(data, "validation_url", None),
            "stk_callback_url": getattr(data, "stk_callback_url", None),
            "connected": bool(conf) or status == "connected",
        }


class RegisterUrlsRequest(BaseModel):
    confirmation_url: str
    validation_url: str
    response_type: Literal["Completed", "Cancelled"] = "Completed"
