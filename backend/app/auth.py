"""Merchant-scoped HTTP Basic authentication for M2M clients.

Clients use their public client ID as the Basic username and their one-time
issued secret as the password. Merchant scope is derived from the database,
never from request input.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import get_session
from app.models import M2MClient, Merchant
from app.security import verify_client_secret

_basic = HTTPBasic(auto_error=False)


@dataclass(frozen=True, slots=True)
class MerchantPrincipal:
    merchant_id: UUID
    client_id: str
    scopes: frozenset[str]


async def get_principal(
    credentials: HTTPBasicCredentials | None = Depends(_basic),
    session: AsyncSession = Depends(get_session),
) -> MerchantPrincipal:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid client credentials",
        headers={"WWW-Authenticate": "Basic"},
    )
    if credentials is None:
        raise unauthorized

    statement = (
        select(M2MClient, Merchant)
        .join(Merchant, Merchant.id == M2MClient.merchant_id)
        .where(M2MClient.client_id == credentials.username)
    )
    result = await session.exec(statement)
    row = result.first()
    if row is None:
        raise unauthorized
    client, merchant = row
    if client.status != "active" or merchant.status != "active":
        raise unauthorized
    if not verify_client_secret(credentials.password, client.secret_hash):
        raise unauthorized

    client.last_used_at = datetime.now(timezone.utc)
    await session.commit()
    return MerchantPrincipal(
        merchant_id=merchant.id,
        client_id=client.client_id,
        scopes=frozenset(client.scopes),
    )


def require_scope(scope: str):
    async def check_scope(principal: MerchantPrincipal = Depends(get_principal)) -> MerchantPrincipal:
        if scope not in principal.scopes and "*" not in principal.scopes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient scope")
        return principal

    return check_scope
