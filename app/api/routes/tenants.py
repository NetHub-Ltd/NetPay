from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.api.deps import get_session, require_admin
from app.core.security import hash_password
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.tenant import AssignUserRequest, TenantCreate, TenantOut

router = APIRouter(prefix="/v1/tenants", tags=["tenants"])

@router.get("", response_model=list[TenantOut])
async def list_tenants(session: Annotated[AsyncSession, Depends(get_session)], _: Annotated[User, Depends(require_admin)]) -> list[Tenant]:
    r = await session.exec(select(Tenant).order_by(Tenant.created_at.desc()))
    return list(r.all())

@router.post("", response_model=TenantOut, status_code=status.HTTP_201_CREATED)
async def create_tenant(body: TenantCreate, session: Annotated[AsyncSession, Depends(get_session)], admin: Annotated[User, Depends(require_admin)]) -> Tenant:
    existing = await session.exec(select(Tenant).where(Tenant.slug == body.slug))
    if existing.first():
        raise HTTPException(status_code=400, detail="Slug already exists")
    t = Tenant(name=body.name, slug=body.slug, created_by=admin.id)
    session.add(t)
    await session.commit()
    await session.refresh(t)
    return t

@router.post("/assign-user", response_model=dict)
async def assign_user(body: AssignUserRequest, session: Annotated[AsyncSession, Depends(get_session)], _: Annotated[User, Depends(require_admin)]) -> dict:
    tr = await session.exec(select(Tenant).where(Tenant.id == body.tenant_id))
    if not tr.first():
        raise HTTPException(status_code=404, detail="Tenant not found")
    ur = await session.exec(select(User).where(User.email == body.email.lower()))
    user = ur.first()
    if user:
        user.tenant_id = body.tenant_id
        user.role = "user"
        session.add(user)
    else:
        user = User(email=body.email.lower(), hashed_password=hash_password(body.password),
                    display_name=body.display_name, role="user", tenant_id=body.tenant_id, is_active=True)
        session.add(user)
    await session.commit()
    return {"ok": True, "email": body.email.lower(), "tenant_id": str(body.tenant_id)}
