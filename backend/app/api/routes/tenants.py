from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_session, require_admin
from app.crud.tenant import tenant_crud
from app.models.tenant import Tenant
from app.schemas.principal import Principal
from app.schemas.tenant import TenantCreate, TenantOut

router = APIRouter(prefix="/v1/tenants", tags=["tenants"])


@router.get("", response_model=list[TenantOut])
async def list_tenants(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[Principal, Depends(require_admin)],
) -> list[Tenant]:
    return list(await tenant_crud.list_all(session))


@router.post("", response_model=TenantOut, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    body: TenantCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    admin: Annotated[Principal, Depends(require_admin)],
) -> Tenant:
    existing = await tenant_crud.get_by_slug(session, body.slug)
    if existing:
        raise HTTPException(status_code=400, detail="Slug already exists")
    if body.id is not None:
        by_id = await tenant_crud.get(session, body.id)
        if by_id:
            raise HTTPException(status_code=400, detail="Tenant id already exists")
    t = await tenant_crud.create_tenant(
        session,
        name=body.name,
        slug=body.slug,
        created_by=admin.id,
        id=body.id,
    )
    await session.commit()
    await session.refresh(t)
    return t
