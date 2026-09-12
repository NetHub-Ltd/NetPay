"""Shared test helpers — credentials come from env set in conftest (fixture-only)."""
from __future__ import annotations

import os
from typing import Any

from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlmodel import Session, select

from app.core.config import settings
from app.core.security import hash_password
from app.models.integration import Credential, Integration
from app.models.tenant import Tenant
from app.models.user import User

# Never hardcode password/api-key literals in individual tests.
FIXTURE_USER_PASSWORD = os.environ["TEST_USER_PASSWORD"]
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@nethub.test")
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]


def internal_headers() -> dict[str, str]:
    return {"X-Internal-Api-Key": settings.internal_api_key}


def fixture_provider_credentials() -> list[tuple[str, str]]:
    """Placeholder M-Pesa credential rows for sandbox tests (not real Daraja secrets)."""
    return [
        ("consumer_key", "fixture-mpesa-consumer-key"),
        ("consumer_secret", "fixture-mpesa-consumer-secret"),
        ("passkey", "fixture-mpesa-passkey"),
    ]


async def login(client: AsyncClient, email: str, password: str) -> str:
    res = await client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


async def login_admin(client: AsyncClient) -> str:
    return await login(client, ADMIN_EMAIL, ADMIN_PASSWORD)


def seed_tenant_user_integration(
    *,
    slug: str,
    email: str,
    public_id: str,
) -> dict[str, Any]:
    """Idempotent seed via sync engine for payment tests."""
    engine = create_engine(settings.sync_database_url)
    with Session(engine) as session:
        admin = session.exec(select(User).where(User.email == ADMIN_EMAIL)).first()
        assert admin is not None
        tenant = session.exec(select(Tenant).where(Tenant.slug == slug)).first()
        if not tenant:
            tenant = Tenant(name=slug, slug=slug, status="active", created_by=admin.id)
            session.add(tenant)
            session.commit()
            session.refresh(tenant)
        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            user = User(
                email=email,
                hashed_password=hash_password(FIXTURE_USER_PASSWORD),
                role="user",
                tenant_id=tenant.id,
                is_active=True,
            )
            session.add(user)
            session.commit()
        integ = session.exec(select(Integration).where(Integration.public_id == public_id)).first()
        if not integ:
            integ = Integration(
                tenant_id=tenant.id,
                public_id=public_id,
                shortcode="174379",
                type="paybill",
                environment="sandbox",
                status="active",
            )
            session.add(integ)
            session.commit()
            session.refresh(integ)
            for kind, val in fixture_provider_credentials():
                session.add(Credential(integration_id=integ.id, kind=kind, value=val))
            session.commit()
        out = {"tenant_id": str(tenant.id), "public_id": public_id, "email": email}
    engine.dispose()
    return out
