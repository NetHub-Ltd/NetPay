from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.user import User
from app.services.edge_status import get_edge_connection_status

router = APIRouter(prefix="/v1/system", tags=["system"])


@router.get("/edge-connection")
async def edge_connection(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """How recently the M-Pesa edge worker reached NetPay."""
    _ = user
    return await get_edge_connection_status(session)
