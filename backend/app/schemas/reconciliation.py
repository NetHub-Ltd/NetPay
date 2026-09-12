from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ReconciliationExceptionOut(BaseModel):
    id: UUID
    tenant_id: Optional[UUID] = None
    payment_intent_id: Optional[UUID] = None
    kind: str
    status: str
    provider_ref: Optional[str] = None
    message: str
    resolved_note: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class ResolveBody(BaseModel):
    resolved_note: str = Field(default="Resolved by operator", max_length=512)
