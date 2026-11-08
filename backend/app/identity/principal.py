"""Principal derived from NetHubKe UserRead — not an M2M merchant client."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class HumanPrincipal:
    """Authenticated human resolved through NetHubKe; no local password store."""

    id: UUID
    email: str
    full_name: str = ""
    username: str = ""
    is_active: bool = True
    is_admin: bool = False
    tenant_id: UUID | None = None
