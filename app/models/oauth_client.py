from __future__ import annotations
from uuid import UUID
from sqlmodel import Field
from app.models.base import BaseMixin

class OAuthClient(BaseMixin, table=True):
    __tablename__ = "oauth_clients"
    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    client_id: str = Field(index=True, unique=True, max_length=64)
    client_secret_hash: str
    name: str = Field(max_length=120)
    is_active: bool = Field(default=True)
