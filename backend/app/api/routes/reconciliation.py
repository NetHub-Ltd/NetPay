from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import can_access_tenant, get_current_user, get_session, require_admin
from app.crud.reconciliation import reconciliation_crud
from app.models.user import User
from app.schemas.reconciliation import ReconciliationExceptionOut, ResolveBody
from app.services.reconciliation import run_reconciliation_scan

router = APIRouter(prefix="/v1/reconciliation", tags=["reconciliation"])


@router.get("/exceptions", response_model=list[ReconciliationExceptionOut])
async def list_exceptions(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> list:
    """Open reconciliation exceptions for your tenant (admin sees all)."""
    return list(
        await reconciliation_crud.list_open(
            session,
            tenant_id=user.tenant_id,
            is_admin=user.role == "admin",
        )
    )


@router.post("/scan", response_model=dict)
async def trigger_scan(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(require_admin)],
) -> dict:
    """Admin: run internal consistency scan and open new exceptions."""
    return await run_reconciliation_scan(session)


@router.post("/exceptions/{exception_id}/resolve", response_model=ReconciliationExceptionOut)
async def resolve_exception(
    exception_id: UUID,
    body: ResolveBody,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    row = await reconciliation_crud.get(session, exception_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    if row.tenant_id and not can_access_tenant(user, row.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    if user.role != "admin" and not row.tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = await reconciliation_crud.update(
        session,
        db_obj=row,
        obj_in={"status": "resolved", "resolved_note": body.resolved_note[:512]},
    )
    await session.commit()
    await session.refresh(updated)
    return updated
