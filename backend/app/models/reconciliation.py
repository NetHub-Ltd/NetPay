"""Reconciliation exception queue (P1-B)."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlmodel import Field

from app.models.base import BaseMixin


class ReconciliationException(BaseMixin, table=True):
    __tablename__ = "reconciliation_exceptions"

    tenant_id: Optional[UUID] = Field(default=None, foreign_key="tenants.id", index=True)
    payment_intent_id: Optional[UUID] = Field(default=None, foreign_key="payment_intents.id", index=True)
    kind: str = Field(max_length=64, index=True)
    # unmatched_provider | unmatched_netpay | amount_mismatch | stale_pending | note
    status: str = Field(default="open", max_length=32, index=True)  # open | resolved
    provider_ref: Optional[str] = Field(default=None, max_length=128, index=True)
    message: str = Field(max_length=512)
    details_json: Optional[str] = Field(default=None)
    resolved_note: Optional[str] = Field(default=None, max_length=512)
