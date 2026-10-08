from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.schemas.auth import UserOut
from app.schemas.principal import Principal

router = APIRouter(tags=["auth"])


@router.get("/auth/me", response_model=UserOut)
async def me(user: Annotated[Principal, Depends(get_current_user)]) -> UserOut:
    """Return the NetHub identity for this Bearer token (no local user store)."""
    display = (user.full_name or user.username or "").strip() or None
    return UserOut(
        id=user.id,
        email=user.email,
        display_name=display,
        full_name=(user.full_name or "").strip() or None,
        username=(user.username or "").strip() or None,
        role=user.role,
        tenant_id=user.tenant_id,
        tenant_name=user.tenant_name,
        tenant_tier=user.tenant_tier,
        is_active=user.is_active,
    )
