from __future__ import annotations
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.api.deps import can_access_tenant, get_current_user, get_session
from app.core.config import settings
from app.models.user import User
from app.models.webhook import Webhook
from app.schemas.webhook import WebhookCreate, WebhookOut
from app.services.events import record_event
from app.services.ids import new_id
from app.services.webhooks import probe_webhook_liveness

router = APIRouter(prefix="/v1/webhooks", tags=["webhooks"])

@router.get("", response_model=list[WebhookOut])
async def list_webhooks(tenant_id: UUID, session: Annotated[AsyncSession, Depends(get_session)], user: Annotated[User, Depends(get_current_user)]) -> list[Webhook]:
    if not can_access_tenant(user, tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    result = await session.exec(select(Webhook).where(Webhook.tenant_id == tenant_id).order_by(Webhook.created_at))
    return list(result.all())

@router.post("", response_model=WebhookOut, status_code=status.HTTP_201_CREATED)
async def create_webhook(body: WebhookCreate, session: Annotated[AsyncSession, Depends(get_session)], user: Annotated[User, Depends(get_current_user)]) -> Webhook:
    if not can_access_tenant(user, body.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    count_r = await session.exec(select(func.count()).select_from(Webhook).where(Webhook.tenant_id == body.tenant_id))
    if count_r.one() >= settings.max_webhooks_per_tenant:
        raise HTTPException(status_code=400, detail=f"Maximum {settings.max_webhooks_per_tenant} webhooks per client")
    url = str(body.url)
    if not url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Webhook URL must be HTTPS")
    secret = new_id("whsec")
    await probe_webhook_liveness(url, secret)
    hook = Webhook(tenant_id=body.tenant_id, url=url, secret=secret, last_live_at=datetime.now(timezone.utc))
    session.add(hook)
    await session.commit()
    await session.refresh(hook)
    await record_event(session, tenant_id=body.tenant_id, category="webhook", action="webhook.added", message=f"Webhook live: {url}")
    return hook

@router.delete("/{webhook_id}")
async def delete_webhook(webhook_id: UUID, session: Annotated[AsyncSession, Depends(get_session)], user: Annotated[User, Depends(get_current_user)]) -> dict:
    result = await session.exec(select(Webhook).where(Webhook.id == webhook_id))
    hook = result.first()
    if not hook:
        raise HTTPException(status_code=404, detail="Not found")
    if not can_access_tenant(user, hook.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    await session.delete(hook)
    await session.commit()
    return {"ok": True}
