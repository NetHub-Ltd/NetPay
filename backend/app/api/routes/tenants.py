from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_session, require_admin
from app.core.security import hash_password
from app.crud.tenant import tenant_crud
from app.crud.user import user_crud
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.tenant import AssignUserRequest, TenantCreate, TenantOut

router = APIRouter(prefix="/v1/tenants", tags=["tenants"])


@router.get("", response_model=list[TenantOut])
async def list_tenants(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[User, Depends(require_admin)],
) -> list[Tenant]:
    return list(await tenant_crud.list_all(session))


@router.post("", response_model=TenantOut, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    body: TenantCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    admin: Annotated[User, Depends(require_admin)],
) -> Tenant:
    existing = await tenant_crud.get_by_slug(session, body.slug)
    if existing:
        raise HTTPException(status_code=400, detail="Slug already exists")
    t = await tenant_crud.create_tenant(
        session, name=body.name, slug=body.slug, created_by=admin.id
    )
    await session.commit()
    await session.refresh(t)
    return t


@router.post("/assign-user", response_model=dict)
async def assign_user(
    body: AssignUserRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[User, Depends(require_admin)],
) -> dict:
    tenant = await tenant_crud.get(session, body.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    user = await user_crud.get_by_email(session, body.email.lower())
    if user:
        await user_crud.update(
            session,
            db_obj=user,
            obj_in={"tenant_id": body.tenant_id, "role": "user"},
        )
    else:
        await user_crud.create(
            session,
            obj_in={
                "email": body.email.lower(),
                "hashed_password": hash_password(body.password),
                "display_name": body.display_name,
                "role": "user",
                "tenant_id": body.tenant_id,
                "is_active": True,
            },
        )
    await session.commit()
    return {"ok": True, "email": body.email.lower(), "tenant_id": str(body.tenant_id)}
