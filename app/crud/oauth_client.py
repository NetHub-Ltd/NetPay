from __future__ import annotations

from typing import Optional, Type
from uuid import UUID

from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud.base import BaseCRUD
from app.models.oauth_client import OAuthClient


class OAuthClientCreateIn(BaseModel):
    tenant_id: UUID
    client_id: str
    client_secret_hash: str
    name: str
    is_active: bool = True


class OAuthClientUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    client_secret_hash: Optional[str] = None


class OAuthClientCRUD(BaseCRUD[OAuthClient, OAuthClientCreateIn, OAuthClientUpdate]):
    def __init__(self, model: Type[OAuthClient] = OAuthClient):
        super().__init__(model)

    async def get_active_by_client_id(self, db: AsyncSession, client_id: str) -> Optional[OAuthClient]:
        rows = await self.get_by_attributes(
            db, filters={"client_id": client_id, "is_active": True}, limit=1
        )
        return rows[0] if rows else None


oauth_client_crud = OAuthClientCRUD(OAuthClient)
