"""Human identity endpoints (NetHubKe-backed)."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.identity.deps import get_human_principal
from app.identity.principal import HumanPrincipal

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class HumanMeOut(BaseModel):
    id: UUID
    email: str
    full_name: str = ""
    username: str = ""
    is_active: bool = True
    is_admin: bool = False
    tenant_id: UUID | None = None
    auth_type: str = Field(default="human_nethub", description="Discriminator vs M2M")


@router.get("/me", response_model=HumanMeOut)
async def auth_me(
    principal: Annotated[HumanPrincipal, Depends(get_human_principal)],
) -> HumanMeOut:
    """Return the NetHubKe-resolved human for this IdP access token."""
    return HumanMeOut(
        id=principal.id,
        email=principal.email,
        full_name=principal.full_name,
        username=principal.username,
        is_active=principal.is_active,
        is_admin=principal.is_admin,
        tenant_id=principal.tenant_id,
        auth_type="human_nethub",
    )
