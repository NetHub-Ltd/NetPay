"""Private persistence endpoints for Next.js BFF sessions.

These endpoints are service-to-service only. Never expose /internal/* through
public ingress; the shared secret is an additional authentication boundary.
"""
from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Depends, Header, HTTPException, Path, Response, status
from sqlalchemy import select, update
from pydantic import BaseModel, Field, SecretStr
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.models.bff_sessions import BFFSession

router = APIRouter(prefix="/internal/v1/bff/sessions", tags=["internal"], include_in_schema=False)


class BFFSessionWrite(BaseModel):
    session_id_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    access_token: SecretStr
    refresh_token: SecretStr | None = None
    access_expires_at: datetime
    expires_at: datetime


class BFFSessionUpdate(BaseModel):
    expected_version: int = Field(ge=1)
    access_token: SecretStr
    refresh_token: SecretStr | None = None
    access_expires_at: datetime
    expires_at: datetime


class BFFSessionRead(BaseModel):
    version: int
    access_token: str
    refresh_token: str | None
    access_expires_at: datetime
    expires_at: datetime


def _fernet() -> Fernet:
    value = get_settings().bff_session_encryption_key
    if value is None:
        raise HTTPException(status_code=503, detail="bff_session_store_unavailable")
    try:
        return Fernet(value.get_secret_value().encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise HTTPException(status_code=503, detail="bff_session_store_misconfigured") from exc


def _encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("ascii")


def _decrypt(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeEncodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=503, detail="bff_session_store_unavailable") from exc


async def require_bff_internal_secret(
    supplied: Annotated[str | None, Header(alias="X-NetPay-BFF-Secret")] = None,
) -> None:
    expected = get_settings().bff_internal_secret
    if expected is None or len(expected.get_secret_value()) < 32:
        raise HTTPException(status_code=503, detail="bff_internal_auth_not_configured")
    if supplied is None or not secrets.compare_digest(
        supplied, expected.get_secret_value()
    ):
        raise HTTPException(status_code=401, detail="bff_internal_auth_required")


def _validate_expiry(access_expires_at: datetime, expires_at: datetime) -> None:
    now = datetime.now(UTC)
    if access_expires_at.tzinfo is None or expires_at.tzinfo is None:
        raise HTTPException(status_code=422, detail="session_expiry_must_be_timezone_aware")
    if access_expires_at <= now or expires_at <= now:
        raise HTTPException(status_code=422, detail="session_expiry_must_be_in_future")
    if expires_at > now + timedelta(hours=8, minutes=1):
        raise HTTPException(status_code=422, detail="session_lifetime_exceeds_policy")


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_bff_internal_secret)],
)
async def create_bff_session(
    body: BFFSessionWrite,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, str]:
    _validate_expiry(body.access_expires_at, body.expires_at)
    existing = await session.get(BFFSession, body.session_id_hash)
    if existing is not None:
        raise HTTPException(status_code=409, detail="session_already_exists")
    now = datetime.now(UTC)
    row = BFFSession(
        session_id_hash=body.session_id_hash,
        access_token_ciphertext=_encrypt(body.access_token.get_secret_value()),
        refresh_token_ciphertext=(
            _encrypt(body.refresh_token.get_secret_value()) if body.refresh_token else None
        ),
        access_expires_at=body.access_expires_at.astimezone(UTC),
        expires_at=body.expires_at.astimezone(UTC),
        created_at=now,
        updated_at=now,
        version=1,
        revoked_at=None,
    )
    session.add(row)
    await session.commit()
    return {"status": "created"}


@router.get(
    "/ready",
    dependencies=[Depends(require_bff_internal_secret)],
)
async def bff_session_store_ready(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, str]:
    """Internal readiness: DB table and token-encryption key must both be usable."""
    _fernet()
    try:
        await session.execute(select(BFFSession.session_id_hash).limit(1))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="bff_session_store_unavailable") from exc
    return {"status": "ok"}


@router.get(
    "/{session_id_hash}",
    response_model=BFFSessionRead,
    dependencies=[Depends(require_bff_internal_secret)],
)
async def read_bff_session(
    session_id_hash: Annotated[str, Path(pattern=r"^[a-f0-9]{64}$")],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BFFSessionRead:
    row = await session.get(BFFSession, session_id_hash)
    now = datetime.now(UTC)
    if row is None or row.revoked_at is not None or row.deleted_at is not None:
        raise HTTPException(status_code=404, detail="session_not_found")
    if row.expires_at <= now:
        row.revoked_at = now
        row.deleted_at = now
        row.access_token_ciphertext = ""
        row.refresh_token_ciphertext = None
        row.updated_at = now
        session.add(row)
        await session.commit()
        raise HTTPException(status_code=404, detail="session_not_found")
    return BFFSessionRead(
        version=row.version,
        access_token=_decrypt(row.access_token_ciphertext),
        refresh_token=(
            _decrypt(row.refresh_token_ciphertext) if row.refresh_token_ciphertext else None
        ),
        access_expires_at=row.access_expires_at,
        expires_at=row.expires_at,
    )


@router.patch(
    "/{session_id_hash}",
    dependencies=[Depends(require_bff_internal_secret)],
)
async def update_bff_session(
    session_id_hash: Annotated[str, Path(pattern=r"^[a-f0-9]{64}$")],
    body: BFFSessionUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, str]:
    _validate_expiry(body.access_expires_at, body.expires_at)
    now = datetime.now(UTC)
    statement = (
        update(BFFSession)
        .where(
            BFFSession.session_id_hash == session_id_hash,
            BFFSession.version == body.expected_version,
            BFFSession.revoked_at.is_(None),
            BFFSession.deleted_at.is_(None),
            BFFSession.expires_at > now,
        )
        .values(
            access_token_ciphertext=_encrypt(body.access_token.get_secret_value()),
            refresh_token_ciphertext=(
                _encrypt(body.refresh_token.get_secret_value())
                if body.refresh_token is not None
                else BFFSession.refresh_token_ciphertext
            ),
            access_expires_at=body.access_expires_at.astimezone(UTC),
            expires_at=body.expires_at.astimezone(UTC),
            version=BFFSession.version + 1,
            updated_at=now,
        )
    )
    result = await session.execute(statement)
    if result.rowcount != 1:
        existing = await session.get(BFFSession, session_id_hash)
        if existing is None or existing.revoked_at is not None or existing.expires_at <= now:
            raise HTTPException(status_code=404, detail="session_not_found")
        raise HTTPException(status_code=409, detail="session_version_conflict")
    await session.commit()
    return {"status": "updated", "version": str(body.expected_version + 1)}


@router.delete(
    "/{session_id_hash}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_bff_internal_secret)],
)
async def revoke_bff_session(
    session_id_hash: Annotated[str, Path(pattern=r"^[a-f0-9]{64}$")],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    now = datetime.now(UTC)
    statement = (
        update(BFFSession)
        .where(
            BFFSession.session_id_hash == session_id_hash,
            BFFSession.revoked_at.is_(None),
            BFFSession.deleted_at.is_(None),
        )
        .values(
            revoked_at=now,
            deleted_at=now,
            deleted_at=now,
            access_token_ciphertext="",
            refresh_token_ciphertext=None,
            updated_at=now,
        )
    )
    await session.execute(statement)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
