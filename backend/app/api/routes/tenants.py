from __future__ import annotations

import re
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import can_access_tenant, get_current_user, get_session, require_admin
from app.crud.tenant import tenant_crud
from app.crud.user import user_crud
from app.models.tenant import Tenant
from app.schemas.principal import Principal
from app.schemas.tenant import TenantCreate, TenantOut

router = APIRouter(prefix="/v1/tenants", tags=["tenants"])


def _slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.strip().lower())
    s = s.strip("-")[:40] or "business"
    return s


@router.get("", response_model=list[TenantOut])
async def list_tenants(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[Principal, Depends(require_admin)],
) -> list[Tenant]:
    stmt = (
        select(Tenant)
        .where(col(Tenant.deleted_at).is_(None))
        .order_by(col(Tenant.created_at).desc())
        .limit(200)
    )
    return list((await session.exec(stmt)).all())


@router.get("/{tenant_id}", response_model=TenantOut)
async def get_tenant(
    tenant_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[Principal, Depends(get_current_user)],
) -> Tenant:
    t = await tenant_crud.get(session, tenant_id)
    if not t or getattr(t, "deleted_at", None) is not None:
        raise HTTPException(status_code=404, detail="Business not found")
    if not can_access_tenant(user, t.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return t


@router.post("", response_model=TenantOut, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    body: TenantCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    admin: Annotated[Principal, Depends(require_admin)],
) -> Tenant:
    if not body.slug:
        raise HTTPException(status_code=400, detail="Slug is required")
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


@router.post("/self", response_model=TenantOut, status_code=status.HTTP_201_CREATED)
async def self_register_business(
    body: TenantCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[Principal, Depends(get_current_user)],
) -> Tenant:
    """Free tier: non-admin with no business may create exactly one."""
    if user.is_admin:
        raise HTTPException(
            status_code=400,
            detail="Admins should use the standard business create endpoint.",
        )
    if user.tenant_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Your account is already linked to a business.",
        )

    local = await user_crud.get_active_by_id(session, user.id)
    if local is None:
        local = await user_crud.get_by_email(session, user.email)
    if local and local.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="Your account is already linked to a business.",
        )

    slug = (body.slug or _slugify(body.name)).lower()
    existing = await tenant_crud.get_by_slug(session, slug)
    if existing:
        slug = f"{slug}-{str(uuid4())[:8]}"

    t = await tenant_crud.create_tenant(
        session,
        name=body.name.strip(),
        slug=slug,
        created_by=user.id,
        id=body.id,
    )

    if local:
        await user_crud.update(
            session,
            db_obj=local,
            obj_in={"tenant_id": t.id, "display_name": user.full_name or local.display_name},
        )
    else:
        await user_crud.create(
            session,
            obj_in={
                "id": user.id,
                "email": user.email.lower(),
                "hashed_password": None,
                "display_name": user.full_name or None,
                "role": "user",
                "tenant_id": t.id,
                "is_active": True,
            },
        )

    await session.commit()
    await session.refresh(t)
    return t
