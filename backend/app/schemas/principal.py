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
    # Set by NetPay from ADMIN_EMAIL allowlist — not from IdP roles
    is_admin: bool = False

    @property
    def role(self) -> str:
        return "admin" if self.is_admin else "user"
