from __future__ import annotations

from typing import Optional, Type
from uuid import UUID

from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud.base import BaseCRUD
from app.models.user import User


class UserCreate(BaseModel):
    email: str
    hashed_password: str
    display_name: Optional[str] = None
    role: str = "user"
    tenant_id: Optional[UUID] = None
    is_active: bool = True


class UserUpdate(BaseModel):
    email: Optional[str] = None
    hashed_password: Optional[str] = None
    display_name: Optional[str] = None
    role: Optional[str] = None
    tenant_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class UserCRUD(BaseCRUD[User, UserCreate, UserUpdate]):
    def __init__(self, model: Type[User] = User):
        super().__init__(model)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        rows = await self.get_by_attributes(db, filters={"email": email.lower()}, limit=1)
        return rows[0] if rows else None

    async def get_active_by_id(self, db: AsyncSession, id: UUID) -> Optional[User]:
        rows = await self.get_by_attributes(
            db, filters={"id": id, "is_active": True}, limit=1
        )
        return rows[0] if rows else None


user_crud = UserCRUD(User)
