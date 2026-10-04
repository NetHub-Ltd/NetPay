from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import can_access_tenant, get_current_user, get_session, user_can_access_tenant
from app.crud.integration import credential_crud, integration_crud
from app.models.integration import Integration
from app.schemas.principal import Principal
from app.providers.mpesa import get_access_token, register_c2b_urls
from app.schemas.integration import IntegrationCreate, IntegrationOut, RegisterUrlsRequest
from app.services.events import record_event
from app.services.ids import new_id

router = APIRouter(prefix="/v1/integrations", tags=["integrations"])


async def load_creds(session: AsyncSession, integration_id: UUID) -> dict[str, str]:
    return await credential_crud.map_for_integration(session, integration_id)


@router.get("", response_model=list[IntegrationOut])
async def list_integrations(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[Principal, Depends(get_current_user)],
) -> list[Integration]:
    if user.is_admin:
        return list(
            await integration_crud.list_active(
                session, tenant_id=None, is_admin=True
            )
        )
    # Collect tenant ids this principal can use (primary + owned)
    from sqlmodel import col, or_, select
    from app.models.tenant import Tenant

    clauses = [col(Tenant.created_by) == user.id]
    if user.tenant_id is not None:
        clauses.append(col(Tenant.id) == user.tenant_id)
    stmt = (
        select(Tenant.id)
        .where(col(Tenant.deleted_at).is_(None))
        .where(or_(*clauses))
    )
    tenant_ids = list((await session.exec(stmt)).all())
    if not tenant_ids:
        return []
    items = []
    for tid in tenant_ids:
        items.extend(
            await integration_crud.list_active(
                session, tenant_id=tid, is_admin=False
            )
        )
    return items


@router.get("/{integration_id}", response_model=IntegrationOut)
async def get_integration(
    integration_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[Principal, Depends(get_current_user)],
) -> Integration:
    integ = await integration_crud.get(session, integration_id)
    if not integ or getattr(integ, "deleted_at", None) is not None:
        raise HTTPException(status_code=404, detail="Shortcode not found")
    if not await user_can_access_tenant(session, user, integ.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return integ


@router.post("", response_model=IntegrationOut, status_code=status.HTTP_201_CREATED)
async def create_integration(
    body: IntegrationCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[Principal, Depends(get_current_user)],
) -> Integration:
    if not await user_can_access_tenant(session, user, body.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    # Validate Daraja credentials for the chosen environment before persisting.
    try:
        await get_access_token(
            body.consumer_key.strip(),
            body.consumer_secret.strip(),
            body.environment,  # type: ignore[arg-type]
            session=session,
            tenant_id=body.tenant_id,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not verify M-Pesa API credentials for this environment. "
                f"Check consumer key/secret and sandbox vs live. ({str(exc)[:240]})"
            ),
        ) from exc

    pub = new_id("gw")
    integ = await integration_crud.create(
        session,
        obj_in={
            "tenant_id": body.tenant_id,
            "public_id": pub,
            "shortcode": body.shortcode,
            "type": body.type,
            "environment": body.environment,
            "confirmation_url": body.confirmation_url,
            "validation_url": body.validation_url,
            "stk_callback_url": body.stk_callback_url,
            "status": "pending_setup",
        },
    )
    await session.commit()
    await session.refresh(integ)
    for kind, val in [
        ("consumer_key", body.consumer_key),
        ("consumer_secret", body.consumer_secret),
        ("passkey", body.passkey),
    ]:
        await credential_crud.create(
            session,
            obj_in={"integration_id": integ.id, "kind": kind, "value": val},
        )
    await session.commit()
    await record_event(
        session,
        tenant_id=body.tenant_id,
        integration_id=integ.id,
        category="integration",
        action="integration.created",
        message=f"Integration {pub}",
    )
    return integ


@router.post("/{integration_id}/register-urls", response_model=dict)
async def register_urls(
    integration_id: UUID,
    body: RegisterUrlsRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[Principal, Depends(get_current_user)],
) -> dict[str, Any]:
    integ = await integration_crud.get(session, integration_id)
    if not integ:
        raise HTTPException(status_code=404, detail="Not found")
    if not await user_can_access_tenant(session, user, integ.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    creds = await load_creds(session, integ.id)
    if not creds.get("consumer_key") or not creds.get("consumer_secret"):
        raise HTTPException(
            status_code=400,
            detail="Missing Daraja consumer key/secret for this shortcode. Edit credentials and try again.",
        )
    try:
        token = await get_access_token(
            creds["consumer_key"],
            creds["consumer_secret"],
            integ.environment,  # type: ignore[arg-type]
            session=session,
            tenant_id=integ.tenant_id,
            integration_id=integ.id,
        )
        result = await register_c2b_urls(
            shortcode=integ.shortcode,
            confirmation_url=body.confirmation_url,
            validation_url=body.validation_url,
            response_type=body.response_type,
            env=integ.environment,  # type: ignore[arg-type]
            token=token,
            session=session,
            tenant_id=integ.tenant_id,
            integration_id=integ.id,
        )
    except RuntimeError as exc:
        from app.core.logging import logger
        logger.exception("register-urls failed integration={} err={}", integration_id, exc)
        raise HTTPException(status_code=502, detail=str(exc)[:800]) from exc
    await integration_crud.update(
        session,
        db_obj=integ,
        obj_in={
            "confirmation_url": body.confirmation_url,
            "validation_url": body.validation_url,
            "status": "connected",
        },
    )
    await session.commit()
    await record_event(
        session,
        tenant_id=integ.tenant_id,
        integration_id=integ.id,
        category="integration",
        action="c2b.urls_registered",
        message="Daraja C2B URLs registered",
    )
    return {"ok": True, "daraja": result}


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[Principal, Depends(get_current_user)],
) -> None:
    """Retire a paybill/till setup (soft-delete). Callbacks for old checkouts may still settle."""
    integ = await integration_crud.get(session, integration_id)
    if not integ or getattr(integ, "deleted_at", None) is not None:
        raise HTTPException(status_code=404, detail="Not found")
    if not await user_can_access_tenant(session, user, integ.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    await integration_crud.soft_delete(session, id=integration_id)
    await session.commit()
    await record_event(
        session,
        tenant_id=integ.tenant_id,
        integration_id=integ.id,
        category="integration",
        action="integration.retired",
        message=f"Retired shortcode {integ.shortcode} ({integ.public_id})",
    )
