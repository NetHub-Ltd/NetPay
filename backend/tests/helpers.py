"""Shared test helpers — credentials come from env set in conftest (fixture-only)."""
from __future__ import annotations

import os
import uuid
from typing import Any
from uuid import UUID

from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlmodel import Session, select

from app.core.config import settings
from app.core.security import create_test_access_token
from app.models.integration import Credential, Integration
from app.models.tenant import Tenant
from app.models.user import User

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@nethub.test")
ADMIN_KEYCLOAK_ID = UUID(
    os.environ.get("ADMIN_KEYCLOAK_ID", "00000000-0000-4000-8000-000000000001")
)


def internal_headers() -> dict[str, str]:
    return {"X-Internal-Api-Key": settings.internal_api_key}


def fixture_provider_credentials() -> list[tuple[str, str]]:
    """Placeholder M-Pesa credential rows for sandbox tests (not real Daraja secrets)."""
    return [
        ("consumer_key", "fixture-mpesa-consumer-key"),
        ("consumer_secret", "fixture-mpesa-consumer-secret"),
        ("passkey", "fixture-mpesa-passkey"),
    ]


def token_for_user(
    *,
    keycloak_id: UUID,
    email: str,
    role: str = "user",
    tenant_id: UUID | None = None,
) -> str:
    extra: dict[str, Any] = {"email": email, "role": role}
    if tenant_id is not None:
        extra["tenant_id"] = str(tenant_id)
    return create_test_access_token(str(keycloak_id), extra=extra)


async def login(client: AsyncClient, email: str, password: str | None = None) -> str:
    """Issue a test token for a seeded user (password ignored — SSO hard cut)."""
    engine = create_engine(settings.sync_database_url)
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email.lower())).first()
        assert user is not None, f"user {email} not seeded"
        assert user.keycloak_id is not None, f"user {email} missing keycloak_id"
        tok = token_for_user(
            keycloak_id=user.keycloak_id,
            email=user.email,
            role=user.role,
            tenant_id=user.tenant_id,
        )
    engine.dispose()
    return tok


async def login_admin(client: AsyncClient) -> str:
    return await login(client, ADMIN_EMAIL)


def seed_tenant_user_integration(
    *,
    slug: str,
    email: str,
    public_id: str,
    keycloak_id: UUID | None = None,
) -> dict[str, Any]:
    """Idempotent seed via sync engine for payment tests."""
    engine = create_engine(settings.sync_database_url)
    kc = keycloak_id or uuid.uuid4()
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
                hashed_password=None,
                keycloak_id=kc,
                role="user",
                tenant_id=tenant.id,
                is_active=True,
            )
            session.add(user)
            session.commit()
        elif user.keycloak_id is None:
            user.keycloak_id = kc
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
        out = {
            "tenant_id": str(tenant.id),
            "public_id": public_id,
            "email": email,
            "keycloak_id": str(user.keycloak_id or kc),
        }
    engine.dispose()
    return out
