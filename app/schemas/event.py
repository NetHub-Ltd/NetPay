from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class EnvelopeIn(BaseModel):
    """Worker envelope — path routing + normalized payload only."""
    event_id: str = Field(min_length=1)
    provider: str = "mpesa"
    event_type: str = Field(min_length=1)
    integration: dict[str, Any]
    received_at: Optional[str] = None
    request: Optional[dict[str, Any]] = None
    payload: Any = None

class ProcessResult(BaseModel):
    status: str
    message: Optional[str] = None
    intent_id: Optional[UUID] = None
    ResultCode: Optional[str] = None
    ResultDesc: Optional[str] = None

class EventOut(BaseModel):
    id: UUID
    category: str
    action: str
    message: str
    payment_intent_id: Optional[UUID] = None
    is_replayable: bool
    created_at: datetime
    model_config = {"from_attributes": True}
