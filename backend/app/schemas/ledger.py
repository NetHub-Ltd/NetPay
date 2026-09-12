from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class LedgerEntryOut(BaseModel):
    id: UUID
    tenant_id: UUID
    payment_intent_id: UUID
    entry_type: str
    amount_minor: int
    currency: str
    provider_ref: Optional[str] = None
    note: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
