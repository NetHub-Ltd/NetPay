from __future__ import annotations
from typing import Annotated, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.api.deps import can_access_tenant, get_current_user, get_session, require_admin
from app.models.integration import Credential, Integration
from app.models.user import User
from app.providers.mpesa import get_access_token, register_c2b_urls
from app.schemas.integration import IntegrationCreate, IntegrationOut, RegisterUrlsRequest
from app.services.events import record_event
from app.services.ids import new_id

router = APIRouter(prefix="/v1/integrations", tags=["integrations"])

async def load_creds(session: AsyncSession, integration_id: UUID) -> dict[str, str]:
    r = await session.exec(select(Credential).where(Credential.integration_id == integration_id))
    out: dict[str, str] = {}
    for c in r.all():
        out[c.kind] = c.value
    return out

@router.get("", response_model=list[IntegrationOut])
async def list_integrations(session: Annotated[AsyncSession, Depends(get_session)], user: Annotated[User, Depends(get_current_user)]) -> list[Integration]:
    q = select(Integration).where(Integration.deleted_at.is_(None))  # type: ignore
    if user.role != "admin":
        if not user.tenant_id:
            return []
        q = q.where(Integration.tenant_id == user.tenant_id)
    r = await session.exec(q)
    return list(r.all())

@router.post("", response_model=IntegrationOut, status_code=status.HTTP_201_CREATED)
async def create_integration(body: IntegrationCreate, session: Annotated[AsyncSession, Depends(get_session)], user: Annotated[User, Depends(get_current_user)]) -> Integration:
    if not can_access_tenant(user, body.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    pub = new_id("gw")
    integ = Integration(
        tenant_id=body.tenant_id, public_id=pub, shortcode=body.shortcode, type=body.type,
        environment=body.environment, confirmation_url=body.confirmation_url,
        validation_url=body.validation_url, stk_callback_url=body.stk_callback_url,
    )
    session.add(integ)
    await session.commit()
    await session.refresh(integ)
    for kind, val in [("consumer_key", body.consumer_key), ("consumer_secret", body.consumer_secret), ("passkey", body.passkey)]:
        session.add(Credential(integration_id=integ.id, kind=kind, value=val))
    await session.commit()
    await record_event(session, tenant_id=body.tenant_id, integration_id=integ.id, category="integration",
                       action="integration.created", message=f"Integration {pub}")
    return integ

@router.post("/{integration_id}/register-urls", response_model=dict)
async def register_urls(integration_id: UUID, body: RegisterUrlsRequest,
                        session: Annotated[AsyncSession, Depends(get_session)],
                        user: Annotated[User, Depends(get_current_user)]) -> dict[str, Any]:
    r = await session.exec(select(Integration).where(Integration.id == integration_id))
    integ = r.first()
    if not integ:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_access_tenant(user, integ.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    creds = await load_creds(session, integ.id)
    token = await get_access_token(creds["consumer_key"], creds["consumer_secret"], integ.environment)  # type: ignore
    result = await register_c2b_urls(
        shortcode=integ.shortcode, confirmation_url=body.confirmation_url,
        validation_url=body.validation_url, response_type=body.response_type,
        env=integ.environment, token=token,  # type: ignore
    )
    integ.confirmation_url = body.confirmation_url
    integ.validation_url = body.validation_url
    session.add(integ)
    await session.commit()
    await record_event(session, tenant_id=integ.tenant_id, integration_id=integ.id,
                       category="integration", action="c2b.urls_registered", message="Daraja C2B URLs registered")
    return {"ok": True, "daraja": result}
