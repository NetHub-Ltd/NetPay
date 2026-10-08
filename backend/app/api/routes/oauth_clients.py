"""Machine API clients (client credentials) per business — admin only."""
from __future__ import annotations

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user, get_session, user_can_access_tenant
from app.core.security import hash_password
from app.crud.oauth_client import OAuthClientCreateIn, oauth_client_crud
from app.schemas.auth import OAuthClientCreate, OAuthClientOut
from app.schemas.principal import Principal
from app.services.ids import new_client_id, new_client_secret

router = APIRouter(prefix="/v1/oauth/clients", tags=["oauth-clients"])


@router.get("")
async def list_oauth_clients(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[Principal, Depends(get_current_user)],
    tenant_id: Optional[UUID] = Query(default=None),
) -> list[dict]:
    """List clients for a business (secrets never returned)."""
    if tenant_id is None:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    if not await user_can_access_tenant(session, user, tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    from sqlmodel import col, select
    from app.models.oauth_client import OAuthClient

    stmt = (
        select(OAuthClient)
        .where(col(OAuthClient.tenant_id) == tenant_id)
        .where(col(OAuthClient.deleted_at).is_(None))
        .limit(200)
    )
    rows = list((await session.exec(stmt)).all())
    return [
        {
            "client_id": r.client_id,
            "name": r.name,
            "tenant_id": str(r.tenant_id),
            "is_active": r.is_active,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.post("", response_model=OAuthClientOut, status_code=201)
async def create_oauth_client(
    body: OAuthClientCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[Principal, Depends(get_current_user)],
) -> OAuthClientOut:
    """Create a client; secret is returned once."""
    if not await user_can_access_tenant(session, user, body.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    plain = new_client_secret()
    cid = new_client_id()
    await oauth_client_crud.create(
        session,
        obj_in=OAuthClientCreateIn(
            tenant_id=body.tenant_id,
            client_id=cid,
            client_secret_hash=hash_password(plain),
            name=(body.name or "API client").strip()[:120] or "API client",
            is_active=True,
        ),
    )
    await session.commit()
    return OAuthClientOut(
        client_id=cid,
        client_secret=plain,
        name=(body.name or "API client").strip()[:120] or "API client",
        tenant_id=body.tenant_id,
    )


@router.post("/{client_id}/rotate", response_model=OAuthClientOut)
async def rotate_oauth_client_secret(
    client_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[Principal, Depends(get_current_user)],
) -> OAuthClientOut:
    """Rotate secret for an existing client. New secret returned once; old secret stops working."""
    from sqlmodel import col, select
    from app.models.oauth_client import OAuthClient

    stmt = (
        select(OAuthClient)
        .where(col(OAuthClient.client_id) == client_id)
        .where(col(OAuthClient.deleted_at).is_(None))
        .limit(1)
    )
    row = (await session.exec(stmt)).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Client not found")
    if not await user_can_access_tenant(session, user, row.tenant_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    plain = new_client_secret()
    row.client_secret_hash = hash_password(plain)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return OAuthClientOut(
        client_id=row.client_id,
        client_secret=plain,
        name=row.name,
        tenant_id=row.tenant_id,
    )
