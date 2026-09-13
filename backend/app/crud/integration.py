from __future__ import annotations

from typing import Dict, Optional, Sequence, Type
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud.base import BaseCRUD
from app.models.integration import Credential, Integration


class IntegrationCreateIn(BaseModel):
    tenant_id: UUID
    public_id: str
    shortcode: str
    type: str = "paybill"
    environment: str = "sandbox"
    status: str = "active"
    confirmation_url: Optional[str] = None
    validation_url: Optional[str] = None
    stk_callback_url: Optional[str] = None


class IntegrationUpdate(BaseModel):
    deleted_at: Optional[datetime] = None
    shortcode: Optional[str] = None
    type: Optional[str] = None
    environment: Optional[str] = None
    status: Optional[str] = None
    confirmation_url: Optional[str] = None
    validation_url: Optional[str] = None
    stk_callback_url: Optional[str] = None


class CredentialCreateIn(BaseModel):
    integration_id: UUID
    kind: str
    value: str


class CredentialUpdate(BaseModel):
    value: Optional[str] = None


class IntegrationCRUD(BaseCRUD[Integration, IntegrationCreateIn, IntegrationUpdate]):
    def __init__(self, model: Type[Integration] = Integration):
        super().__init__(model)

    async def list_active(
        self,
        db: AsyncSession,
        *,
        tenant_id: Optional[UUID],
        is_admin: bool,
        limit: int = 200,
    ) -> Sequence[Integration]:
        where = [col(self.model.deleted_at).is_(None)]
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

    async def get_by_public_id(
        self, db: AsyncSession, public_id: str, *, include_deleted: bool = False
    ) -> Optional[Integration]:
        rows = await self.get_by_attributes(db, filters={"public_id": public_id}, limit=1)
        if not rows:
            return None
        integ = rows[0]
        if not include_deleted and getattr(integ, "deleted_at", None) is not None:
            return None
        return integ

    async def soft_delete(self, db: AsyncSession, *, id: UUID) -> Optional[Integration]:
        """Mark integration retired (deleted_at)."""
        from datetime import datetime, timezone
        obj = await self.get(db, id)
        if not obj:
            return None
        return await self.update(
            db,
            db_obj=obj,
            obj_in={"deleted_at": datetime.now(timezone.utc)},
        )


class CredentialCRUD(BaseCRUD[Credential, CredentialCreateIn, CredentialUpdate]):
    def __init__(self, model: Type[Credential] = Credential):
        super().__init__(model)

    async def map_for_integration(self, db: AsyncSession, integration_id: UUID) -> Dict[str, str]:
        rows = await self.get_by_attributes(
            db, filters={"integration_id": integration_id}, limit=50
        )
        return {c.kind: c.value for c in rows}


integration_crud = IntegrationCRUD(Integration)
credential_crud = CredentialCRUD(Credential)

