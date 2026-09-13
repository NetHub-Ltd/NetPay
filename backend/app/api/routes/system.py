from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user, get_session
from app.core.config import settings
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


@router.get("/public-config")
async def public_config(
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Non-secret values the SPA needs for setup copy."""
    _ = user
    return {
        "edge_public_base_url": settings.edge_public_base_url.rstrip("/"),
        "edge_callback_path_prefix": settings.edge_callback_path_prefix.rstrip("/") or "/cb",
    }


@router.get("/outbound-requests")
async def list_outbound_requests(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    limit: int = 30,
) -> list[dict[str, Any]]:
    """Recent provider HTTP calls (register URLs, STK, OAuth) for diagnosis."""
    from sqlmodel import col, select

    from app.models.outbound_request import OutboundRequest

    stmt = (
        select(OutboundRequest)
        .where(col(OutboundRequest.deleted_at).is_(None))
        .order_by(col(OutboundRequest.created_at).desc())
        .limit(min(limit, 100))
    )
    if user.role != "admin" and user.tenant_id:
        stmt = stmt.where(OutboundRequest.tenant_id == user.tenant_id)
    rows = list((await session.exec(stmt)).all())
    return [
        {
            "id": str(r.id),
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "operation": r.operation,
            "method": r.method,
            "url": r.url,
            "response_status": r.response_status,
            "success": r.success,
            "error_message": r.error_message,
            "duration_ms": r.duration_ms,
            "response_body": (r.response_body or "")[:400],
        }
        for r in rows
    ]
