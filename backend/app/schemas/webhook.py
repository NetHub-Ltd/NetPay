from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, HttpUrl

class WebhookCreate(BaseModel):
    tenant_id: UUID
    url: HttpUrl

class WebhookOut(BaseModel):
    id: UUID
    tenant_id: UUID
    url: str
    secret: Optional[str] = None
    last_live_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
