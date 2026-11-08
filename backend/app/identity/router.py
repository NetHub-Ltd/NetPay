"""Human identity and membership endpoints (NetHubKe-backed)."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.identity.deps import get_human_principal, require_platform_admin
from app.identity.membership import grant_membership, list_memberships_for_user, revoke_membership
from app.identity.principal import HumanPrincipal
from app.models.merchants import Merchant

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


class MembershipOut(BaseModel):
    merchant_id: UUID
    role: str
    merchant_name: str | None = None
    merchant_slug: str | None = None


class MembershipGrantIn(BaseModel):
    user_id: UUID
    merchant_id: UUID
    role: str = Field(default="member", pattern="^(member|admin)$")


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


@router.get("/memberships", response_model=list[MembershipOut])
async def list_my_memberships(
    principal: Annotated[HumanPrincipal, Depends(get_human_principal)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[MembershipOut]:
    """Merchants this human may access. Empty list means membership still required (no auto-tenant)."""
    rows = await list_memberships_for_user(session, principal.id)
    out: list[MembershipOut] = []
    for row in rows:
        merchant = await session.get(Merchant, row.merchant_id)
        out.append(
            MembershipOut(
                merchant_id=row.merchant_id,
                role=row.role,
                merchant_name=merchant.name if merchant else None,
                merchant_slug=merchant.slug if merchant else None,
            )
        )
    return out


@router.post(
    "/memberships",
    response_model=MembershipOut,
    status_code=status.HTTP_201_CREATED,
)
async def admin_grant_membership(
    body: MembershipGrantIn,
    admin: Annotated[HumanPrincipal, Depends(require_platform_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MembershipOut:
    """Platform admin bootstrap: attach a NetHubKe user to a merchant (no self-serve auto-create)."""
    row = await grant_membership(
        session, user_id=body.user_id, merchant_id=body.merchant_id, role=body.role
    )
    merchant = await session.get(Merchant, row.merchant_id)
    return MembershipOut(
        merchant_id=row.merchant_id,
        role=row.role,
        merchant_name=merchant.name if merchant else None,
        merchant_slug=merchant.slug if merchant else None,
    )


@router.delete("/memberships/{merchant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_revoke_membership(
    merchant_id: UUID,
    user_id: UUID,
    admin: Annotated[HumanPrincipal, Depends(require_platform_admin)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Platform admin: soft-revoke membership."""
    await revoke_membership(session, user_id=user_id, merchant_id=merchant_id)
