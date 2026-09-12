from __future__ import annotations

from typing import Optional, Sequence, Type
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud.base import BaseCRUD
from app.models.reconciliation import ReconciliationException


class ReconCreateIn(BaseModel):
    tenant_id: Optional[UUID] = None
    payment_intent_id: Optional[UUID] = None
    kind: str
    status: str = "open"
    provider_ref: Optional[str] = None
    message: str
    details_json: Optional[str] = None
    resolved_note: Optional[str] = None


class ReconUpdate(BaseModel):
    status: Optional[str] = None
    resolved_note: Optional[str] = None


class ReconciliationCRUD(BaseCRUD[ReconciliationException, ReconCreateIn, ReconUpdate]):
    def __init__(self, model: Type[ReconciliationException] = ReconciliationException):
        super().__init__(model)

    async def list_open(
        self,
        db: AsyncSession,
        *,
        tenant_id: Optional[UUID],
        is_admin: bool,
        limit: int = 100,
    ) -> Sequence[ReconciliationException]:
        where = [col(self.model.status) == "open"]
        if not is_admin:
            if not tenant_id:
                return []
            where.append(col(self.model.tenant_id) == tenant_id)
        items, _ = await self.get_multi_paginated(
            db,
            skip=0,
            limit=limit,
            where_clauses=where,
            sort_by="created_at",
            sort_order="desc",
        )
        return items

    async def find_open_for_intent(
        self,
        db: AsyncSession,
        *,
        payment_intent_id: UUID,
        kind: str,
    ) -> Optional[ReconciliationException]:
        rows = await self.get_by_attributes(
            db,
            filters={
                "payment_intent_id": payment_intent_id,
                "kind": kind,
                "status": "open",
            },
            limit=1,
        )
        return rows[0] if rows else None


reconciliation_crud = ReconciliationCRUD(ReconciliationException)
