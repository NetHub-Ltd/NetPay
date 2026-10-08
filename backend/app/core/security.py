from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(
    subject: str,
    extra: Optional[dict[str, Any]] = None,
    *,
    expires_minutes: Optional[int] = None,
) -> str:
    minutes = expires_minutes if expires_minutes is not None else settings.access_token_expire_minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)

def create_machine_token(
    subject: str,
    extra: Optional[dict[str, Any]] = None,
) -> str:
    """Issue a machine (client_credentials) JWT with audience + shorter TTL."""
    payload_extra: dict[str, Any] = {
        "typ": "machine",
        "aud": settings.machine_token_audience,
    }
    if extra:
        payload_extra.update(extra)
        payload_extra["typ"] = "machine"
        payload_extra["aud"] = settings.machine_token_audience
    return create_access_token(
        subject,
        extra=payload_extra,
        expires_minutes=settings.machine_token_expire_minutes,
    )

def decode_token(token: str, *, audience: Optional[str] = None) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"algorithms": [ALGORITHM]}
    if audience:
        kwargs["audience"] = audience
    return jwt.decode(token, settings.secret_key, **kwargs)
