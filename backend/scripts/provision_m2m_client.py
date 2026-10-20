"""Provision an initial merchant M2M client and print its secret exactly once.

Run only from a trusted operator environment after `alembic upgrade head`.
Set MERCHANT_NAME and DATABASE_URL. The generated client secret is not stored
in plaintext and is printed only so the operator can transfer it securely.
"""

import asyncio
import json
import os
import secrets
from datetime import datetime, timezone

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings
from app.models import M2MClient, Merchant
from app.security import hash_client_secret


async def main() -> None:
    merchant_name = os.environ.get("MERCHANT_NAME", "").strip()
    if not merchant_name:
        raise SystemExit("MERCHANT_NAME is required")

    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    client_id = os.environ.get("NETPAY_CLIENT_ID", f"nph_{secrets.token_urlsafe(12)}")
    client_secret = secrets.token_urlsafe(40)
    scopes = os.environ.get(
        "NETPAY_CLIENT_SCOPES",
        "integrations:read integrations:write payments:read payments:write",
    ).split()
    now = datetime.now(timezone.utc)

    try:
        async with AsyncSession(engine, expire_on_commit=False) as session:
            merchant = Merchant(name=merchant_name, status="active", created_at=now, updated_at=now)
            session.add(merchant)
            await session.flush()
            client = M2MClient(
                merchant_id=merchant.id,
                client_id=client_id,
                secret_hash=hash_client_secret(client_secret),
                scopes=scopes,
                status="active",
                created_at=now,
            )
            session.add(client)
            await session.commit()
            print(json.dumps({
                "merchant_id": str(merchant.id),
                "client_id": client_id,
                "client_secret": client_secret,
                "scopes": scopes,
                "warning": "Store this secret securely; it cannot be retrieved later.",
            }, indent=2))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
