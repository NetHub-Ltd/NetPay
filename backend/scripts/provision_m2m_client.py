"""Provision a merchant and one M2M client for controlled environments.

Run from backend with DATABASE_* settings configured. The generated client secret
is printed once; store it in the consumer's secret manager immediately.
"""
from __future__ import annotations

import argparse
import json
import secrets

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings
from app.core.database import create_database_engine, create_session_factory
from app.models.merchants import M2MClient, Merchant
from app.payments.security import hash_client_secret


async def provision(args: argparse.Namespace) -> None:
    """Create a merchant and a one-time-displayed M2M credential."""
    import asyncio

    engine = create_database_engine(get_settings())
    factory = create_session_factory(engine)
    client_id = "np_" + secrets.token_urlsafe(18)
    client_secret = secrets.token_urlsafe(48)
    try:
        async with factory() as session:  # type: AsyncSession
            merchant = Merchant(name=args.merchant_name, slug=args.merchant_slug)
            session.add(merchant)
            await session.flush()
            client = M2MClient(
                merchant_id=merchant.id,
                client_id=client_id,
                secret_hash=hash_client_secret(client_secret),
                scopes=args.scopes.split(),
                status="active",
            )
            session.add(client)
            await session.commit()
            print(json.dumps({
                "merchant_id": str(merchant.id),
                "client_id": client_id,
                "client_secret": client_secret,
                "scopes": client.scopes,
            }, indent=2))
    finally:
        await engine.dispose()


def main() -> None:
    """Parse arguments and run provisioning."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--merchant-name", required=True)
    parser.add_argument("--merchant-slug", required=True)
    parser.add_argument("--scopes", default="integrations:write payments:write payments:read")
    args = parser.parse_args()
    import asyncio
    asyncio.run(provision(args))


if __name__ == "__main__":
    main()
