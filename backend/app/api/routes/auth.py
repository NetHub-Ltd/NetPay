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
    return UserOut(
        id=user.id,
        email=user.email,
        display_name=user.full_name or user.username or None,
        role=user.role,
        tenant_id=user.tenant_id,
        is_active=user.is_active,
    )
