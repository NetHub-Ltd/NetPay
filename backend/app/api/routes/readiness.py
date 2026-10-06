"""Workspace readiness — single source for overview and setup CTAs."""
from __future__ import annotations

from typing import Annotated, Any, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user, get_session, user_can_access_tenant
from app.crud.integration import integration_crud
from app.models.oauth_client import OAuthClient
from app.models.tenant import Tenant
from app.models.webhook import Webhook
from app.schemas.principal import Principal

router = APIRouter(prefix="/v1/readiness", tags=["readiness"])

NextStep = Literal[
    "create_business",
    "add_shortcode",
    "connect_mpesa",
    "add_notification",
    "connect_system",
    "take_payment",
    "done",
]


class ReadinessOut(BaseModel):
    has_business: bool
    has_shortcode: bool
    has_connected_shortcode: bool
    has_notifications: bool
    has_api_client: bool
    ready_to_collect: bool
    next_step: NextStep
    tenant_id: Optional[UUID] = None
    primary_integration_id: Optional[UUID] = None
    shortcode_count: int = 0
    connected_count: int = 0
    notification_count: int = 0
    api_client_count: int = 0


def _is_connected(integ: Any) -> bool:
    conf = getattr(integ, "confirmation_url", None)
    status = str(getattr(integ, "status", "") or "").lower()
    return bool(conf) or status == "connected"


@router.get("", response_model=ReadinessOut)
async def get_readiness(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[Principal, Depends(get_current_user)],
    tenant_id: Optional[UUID] = Query(default=None),
) -> ReadinessOut:
    """Optional tenant_id scopes to the active business workspace."""
    if tenant_id is not None:
        if not await user_can_access_tenant(session, user, tenant_id):
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        tenant_id = user.tenant_id
        if tenant_id is None and not user.is_admin:
            stmt = (
                select(Tenant)
                .where(col(Tenant.deleted_at).is_(None))
                .where(col(Tenant.created_by) == user.id)
                .order_by(col(Tenant.created_at).desc())
                .limit(1)
            )
            owned = (await session.exec(stmt)).first()
            if owned:
                tenant_id = owned.id

    has_business = tenant_id is not None or user.is_admin

    integrations = list(
        await integration_crud.list_active(
            session,
            tenant_id=tenant_id,
            is_admin=user.is_admin and tenant_id is None,
        )
    )
    if user.is_admin and tenant_id:
        integrations = [i for i in integrations if i.tenant_id == tenant_id]

    has_shortcode = len(integrations) > 0
    connected = [i for i in integrations if _is_connected(i)]
    has_connected = len(connected) > 0
    primary = connected[0] if connected else (integrations[0] if integrations else None)

    webhook_count = 0
    api_client_count = 0
    if tenant_id:
        wstmt = (
            select(Webhook)
            .where(col(Webhook.tenant_id) == tenant_id)
            .where(col(Webhook.deleted_at).is_(None))
        )
        webhook_count = len(list((await session.exec(wstmt)).all()))
        cstmt = (
            select(OAuthClient)
            .where(col(OAuthClient.tenant_id) == tenant_id)
            .where(col(OAuthClient.deleted_at).is_(None))
            .where(col(OAuthClient.is_active).is_(True))
        )
        api_client_count = len(list((await session.exec(cstmt)).all()))

    has_notifications = webhook_count > 0
    has_api_client = api_client_count > 0
    ready = bool(tenant_id and has_shortcode and has_connected)

    if not tenant_id and not user.is_admin:
        next_step: NextStep = "create_business"
    elif not has_shortcode:
        next_step = "add_shortcode"
    elif not has_connected:
        next_step = "connect_mpesa"
    elif not has_notifications:
        next_step = "add_notification"
    elif not has_api_client:
        next_step = "connect_system"
    elif ready:
        next_step = "done"
    else:
        next_step = "take_payment"

    return ReadinessOut(
        has_business=bool(tenant_id) or user.is_admin,
        has_shortcode=has_shortcode,
        has_connected_shortcode=has_connected,
        has_notifications=has_notifications,
        has_api_client=has_api_client,
        ready_to_collect=ready,
        next_step=next_step,
        tenant_id=tenant_id,
        primary_integration_id=primary.id if primary else None,
        shortcode_count=len(integrations),
        connected_count=len(connected),
        notification_count=webhook_count,
        api_client_count=api_client_count,
    )
