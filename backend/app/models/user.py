from __future__ import annotations
from typing import Optional
from uuid import UUID
from sqlmodel import Field
from app.models.base import BaseMixin

class User(BaseMixin, table=True):
    __tablename__ = "users"
    email: str = Field(index=True, unique=True, max_length=255)
    hashed_password: str
    display_name: Optional[str] = Field(default=None, max_length=120)
    role: str = Field(default="user", index=True, max_length=32)
    tenant_id: Optional[UUID] = Field(default=None, index=True)
    is_active: bool = Field(default=True)
