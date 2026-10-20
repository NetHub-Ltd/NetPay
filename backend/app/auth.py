"""Bearer-token authentication and merchant scope enforcement."""

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import get_session
from app.models import M2MClient, Merchant
from app.security import decode_access_token

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class MerchantPrincipal:
    merchant_id: UUID
    client_id: str
    scopes: frozenset[str]


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
) -> MerchantPrincipal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    try:
        claims = decode_access_token(credentials.credentials)
        client_id = claims.get("sub")
        merchant_id_claim = claims.get("mid")
        token_scopes = claims.get("scopes")
        merchant_id = UUID(merchant_id_claim) if isinstance(merchant_id_claim, str) else None
        if not isinstance(client_id, str) or merchant_id is None or not isinstance(token_scopes, list):
            raise _unauthorized()
        if any(not isinstance(scope, str) for scope in token_scopes):
            raise _unauthorized()
    except (JWTError, ValueError):
        raise _unauthorized()

    statement = (
        select(M2MClient, Merchant)
        .join(Merchant, Merchant.id == M2MClient.merchant_id)
        .where(M2MClient.client_id == client_id)
    )
    result = await session.exec(statement)
    row = result.first()
    if row is None:
        raise _unauthorized()
    client, merchant = row
    if client.status != "active" or merchant.status != "active" or merchant.id != merchant_id:
        raise _unauthorized()

    effective_scopes = frozenset(token_scopes).intersection(client.scopes)
    return MerchantPrincipal(merchant_id=merchant.id, client_id=client.client_id, scopes=effective_scopes)


def require_scope(scope: str):
    async def check_scope(principal: MerchantPrincipal = Depends(get_principal)) -> MerchantPrincipal:
        if scope not in principal.scopes and "*" not in principal.scopes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient scope")
        return principal

    return check_scope
