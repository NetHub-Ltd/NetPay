"""Append-only ledger — financial source of truth for settled movements (P0-B)."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import Column, Integer, UniqueConstraint
from sqlmodel import Field

from app.models.base import BaseMixin


class LedgerEntry(BaseMixin, table=True):
    """
    Immutable financial row. Never update amount or type after insert.
    Corrections are compensating entries (future refunds), not edits.
    """

    __tablename__ = "ledger_entries"
    __table_args__ = (
        UniqueConstraint(
            "payment_intent_id",
            "entry_type",
            name="uq_ledger_intent_entry_type",
        ),
    )

    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    payment_intent_id: UUID = Field(foreign_key="payment_intents.id", index=True)
    entry_type: str = Field(max_length=32, index=True)  # collection_credit | …
    amount_minor: int = Field(sa_column=Column(Integer, nullable=False))
    currency: str = Field(default="KES", max_length=8)
    provider_ref: Optional[str] = Field(default=None, max_length=64)
    note: Optional[str] = Field(default=None, max_length=256)
