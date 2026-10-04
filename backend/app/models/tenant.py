from __future__ import annotations
from uuid import UUID
from sqlmodel import Field
from app.models.base import BaseMixin

class Tenant(BaseMixin, table=True):
    __tablename__ = "tenants"
    name: str = Field(max_length=120)
    slug: str = Field(index=True, unique=True, max_length=40)
    status: str = Field(default="active", max_length=32)
    # NetHub principal id or platform admin id — no local users FK (identity is NetHub).
    created_by: UUID = Field(index=True)
