"""Shared test helpers — identity is mocked NetHub principal (see conftest)."""
from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlmodel import Session, select

from app.core.config import settings
from app.models.integration import Credential, Integration
from app.models.tenant import Tenant

ADMIN_EMAIL = "admin@nethub.test"
ADMIN_ID = UUID("00000000-0000-4000-8000-000000000001")
# Default tenant id matches conftest admin/user principal
TENANT_ID = UUID("00000000-0000-4000-8000-0000000000aa")
FIXTURE_USER_PASSWORD = "unused"
ADMIN_PASSWORD = "unused"


def internal_headers() -> dict[str, str]:
    return {"X-Internal-Api-Key": settings.internal_api_key}


def fixture_provider_credentials() -> list[tuple[str, str]]:
    return [
        ("consumer_key", "fixture-mpesa-consumer-key"),
        ("consumer_secret", "fixture-mpesa-consumer-secret"),
        ("passkey", "fixture-mpesa-passkey"),
    ]


async def login_admin(client: AsyncClient) -> str:
    return "test-admin-token"


async def login(client: AsyncClient, email: str, password: str) -> str:
    _ = client, email, password
    return "test-user-token"


def seed_tenant_user_integration(
    *,
    slug: str,
    email: str,
    public_id: str,
    tenant_id: UUID | None = None,
) -> dict[str, Any]:
    """Idempotent seed. Default tenant_id matches conftest principal."""
    _ = email
    tid = tenant_id or TENANT_ID
    engine = create_engine(settings.sync_database_url)
    with Session(engine) as session:
        tenant = session.exec(select(Tenant).where(Tenant.slug == slug)).first()
        if not tenant:
            # Reuse fixed id only if free; otherwise allocate a new UUID
            existing_id = session.get(Tenant, tid)
            use_id = tid if existing_id is None else uuid4()
            tenant = Tenant(
                id=use_id,
                name=slug,
                slug=slug,
                status="active",
                created_by=ADMIN_ID,
            )
            session.add(tenant)
            session.commit()
            session.refresh(tenant)
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
