"""Identity principal resolved from NetHub API (not stored in NetPay)."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Principal(BaseModel):
    """NetHub UserRead-shaped identity for the current request."""

    id: UUID
    email: str
    full_name: str = ""
    username: str = ""
    is_active: bool = True
    tenant_id: Optional[UUID] = None
    tenant_name: Optional[str] = None
    tenant_tier: Optional[str] = None
    # Set by NetHub allowlist or machine client
    is_admin: bool = False
    # Present when authenticated via client_credentials
    client_id: Optional[str] = None

    @property
    def role(self) -> str:
        if self.is_admin:
            return "admin"
        if self.client_id:
            return "machine"
        return "user"

    @property
    def is_machine(self) -> bool:
        return bool(self.client_id)
