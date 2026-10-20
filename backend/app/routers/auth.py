"""OAuth 2.0 client-credentials token endpoint."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import get_session
from app.models import M2MClient, Merchant
from app.schemas import AccessTokenResponse
from app.security import create_access_token, verify_client_secret

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
_basic = HTTPBasic(auto_error=False)


@router.post("/token", response_model=AccessTokenResponse)
async def issue_token(
    grant_type: str = Form(default="client_credentials"),
    credentials: HTTPBasicCredentials | None = Depends(_basic),
    session: AsyncSession = Depends(get_session),
) -> AccessTokenResponse:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid client credentials",
        headers={"WWW-Authenticate": 'Basic realm="NetPay token endpoint"'},
    )
    if grant_type != "client_credentials" or credentials is None:
        raise unauthorized

    result = await session.exec(
        select(M2MClient, Merchant)
        .join(Merchant, Merchant.id == M2MClient.merchant_id)
        .where(M2MClient.client_id == credentials.username)
    )
    row = result.first()
    if row is None:
        raise unauthorized
    client, merchant = row
    if client.status != "active" or merchant.status != "active":
        raise unauthorized
    if not verify_client_secret(credentials.password, client.secret_hash):
        raise unauthorized

    token, expires_in = create_access_token(client.client_id, merchant.id, list(client.scopes))
    client.last_used_at = datetime.now(timezone.utc)
    await session.commit()
    return AccessTokenResponse(
        access_token=token,
        expires_in=expires_in,
        scope=" ".join(client.scopes),
    )
