from __future__ import annotations

from typing import Optional, Sequence, Type
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud.base import BaseCRUD
from app.models.ledger import LedgerEntry


class LedgerEntryCreateIn(BaseModel):
    tenant_id: UUID
    payment_intent_id: UUID
    entry_type: str
    amount_minor: int
    currency: str = "KES"
    provider_ref: Optional[str] = None
    note: Optional[str] = None


class LedgerEntryUpdate(BaseModel):
    """Ledger is append-only — updates are not used."""

    note: Optional[str] = None


class LedgerEntryCRUD(BaseCRUD[LedgerEntry, LedgerEntryCreateIn, LedgerEntryUpdate]):
    def __init__(self, model: Type[LedgerEntry] = LedgerEntry):
        super().__init__(model)

    async def list_for_intent(
        self,
        db: AsyncSession,
        *,
        payment_intent_id: UUID,
        limit: int = 50,
    ) -> Sequence[LedgerEntry]:
        items, _ = await self.get_multi_paginated(
            db,
            skip=0,
            limit=limit,
            where_clauses=[col(self.model.payment_intent_id) == payment_intent_id],
            sort_by="created_at",
            sort_order="asc",
        )
        return items

    async def count_for_intent_type(
        self,
        db: AsyncSession,
        *,
        payment_intent_id: UUID,
        entry_type: str,
    ) -> int:
        rows = await self.get_by_attributes(
            db,
            filters={"payment_intent_id": payment_intent_id, "entry_type": entry_type},
            limit=10,
        )
        return len(rows)


ledger_entry_crud = LedgerEntryCRUD(LedgerEntry)
