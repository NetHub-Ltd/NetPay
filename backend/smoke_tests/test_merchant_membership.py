"""Merchant membership ACL — identity alone is not authorization."""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.identity.deps import get_human_principal, require_platform_admin
from app.identity.membership import ALLOWED_ROLES, require_membership
from app.identity.principal import HumanPrincipal
from app.identity.router import router as identity_router
from app.models.merchants import Merchant, MerchantMember


USER_ID = uuid4()
MERCHANT_ID = uuid4()


def _human(*, is_admin: bool = False, is_active: bool = True) -> HumanPrincipal:
    return HumanPrincipal(
        id=USER_ID,
        email="merchant@example.com",
        full_name="Example",
        username="merchant",
        is_active=is_active,
        is_admin=is_admin,
    )


@pytest.mark.asyncio
async def test_require_membership_missing() -> None:
    session = AsyncMock()
    session.exec = AsyncMock(return_value=MagicMock(first=MagicMock(return_value=None)))
    with pytest.raises(HTTPException) as ei:
        await require_membership(session, user_id=USER_ID, merchant_id=MERCHANT_ID)
    assert ei.value.status_code == 403
    assert ei.value.detail == "merchant_membership_required"


@pytest.mark.asyncio
async def test_require_membership_ok() -> None:
    member = MerchantMember(user_id=USER_ID, merchant_id=MERCHANT_ID, role="member")
    merchant = Merchant(id=MERCHANT_ID, name="Acme", slug="acme", status="active")
    session = AsyncMock()
    session.exec = AsyncMock(return_value=MagicMock(first=MagicMock(return_value=member)))
    session.get = AsyncMock(return_value=merchant)
    row = await require_membership(session, user_id=USER_ID, merchant_id=MERCHANT_ID)
    assert row.role == "member"


@pytest.mark.asyncio
async def test_require_membership_inactive_merchant() -> None:
    member = MerchantMember(user_id=USER_ID, merchant_id=MERCHANT_ID, role="member")
    merchant = Merchant(id=MERCHANT_ID, name="Acme", slug="acme", status="suspended")
    session = AsyncMock()
    session.exec = AsyncMock(return_value=MagicMock(first=MagicMock(return_value=member)))
    session.get = AsyncMock(return_value=merchant)
    with pytest.raises(HTTPException) as ei:
        await require_membership(session, user_id=USER_ID, merchant_id=MERCHANT_ID)
    assert ei.value.status_code == 403
    assert ei.value.detail == "merchant_inactive"


def test_memberships_list_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    app = FastAPI()
    app.include_router(identity_router)

    async def fake_principal() -> HumanPrincipal:
        return _human()

    async def fake_session():
        session = AsyncMock()
        session.exec = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        yield session

    app.dependency_overrides[get_human_principal] = fake_principal
    from app.core.database import get_session

    app.dependency_overrides[get_session] = fake_session

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/auth/memberships",
            headers={"Authorization": "Bearer unused"},
        )
    assert response.status_code == 200
    assert response.json() == []


def test_grant_membership_requires_platform_admin() -> None:
    app = FastAPI()
    app.include_router(identity_router)

    async def fake_principal() -> HumanPrincipal:
        return _human(is_admin=False)

    app.dependency_overrides[get_human_principal] = fake_principal

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/memberships",
            headers={"Authorization": "Bearer unused"},
            json={
                "user_id": str(USER_ID),
                "merchant_id": str(MERCHANT_ID),
                "role": "member",
            },
        )
    assert response.status_code == 403
    assert response.json()["detail"] == "platform_admin_required"



def test_grant_membership_as_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    app = FastAPI()
    app.include_router(identity_router)

    async def fake_principal() -> HumanPrincipal:
        return _human(is_admin=True)

    member = MerchantMember(
        id=uuid4(),
        user_id=USER_ID,
        merchant_id=MERCHANT_ID,
        role="member",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    merchant = Merchant(id=MERCHANT_ID, name="Acme", slug="acme", status="active")

    async def fake_grant(session, **kwargs):
        return member

    async def fake_session():
        session = AsyncMock()
        session.get = AsyncMock(return_value=merchant)
        yield session

    from app.core.database import get_session
    import app.identity.router as router_mod

    monkeypatch.setattr(router_mod, "grant_membership", fake_grant)
    app.dependency_overrides[get_human_principal] = fake_principal
    app.dependency_overrides[get_session] = fake_session

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/memberships",
            headers={"Authorization": "Bearer unused"},
            json={
                "user_id": str(USER_ID),
                "merchant_id": str(MERCHANT_ID),
                "role": "member",
            },
        )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["merchant_id"] == str(MERCHANT_ID)
    assert body["role"] == "member"
    assert body["merchant_name"] == "Acme"


def test_allowed_roles() -> None:
    assert "member" in ALLOWED_ROLES
    assert "admin" in ALLOWED_ROLES


def test_merchant_summary_requires_membership() -> None:
    app = FastAPI()
    app.include_router(identity_router)

    async def fake_principal() -> HumanPrincipal:
        return _human()

    app.dependency_overrides[get_human_principal] = fake_principal

    async def fake_session():
        session = AsyncMock()
        session.exec = AsyncMock(return_value=MagicMock(first=MagicMock(return_value=None)))
        yield session

    from app.core.database import get_session

    app.dependency_overrides[get_session] = fake_session

    with TestClient(app) as client:
        response = client.get(
            f"/api/v1/auth/merchants/{MERCHANT_ID}",
            headers={"Authorization": "Bearer unused"},
        )
    assert response.status_code == 403
    assert response.json()["detail"] == "merchant_membership_required"


def test_merchant_summary_ok_with_membership() -> None:
    app = FastAPI()
    app.include_router(identity_router)

    async def fake_principal() -> HumanPrincipal:
        return _human()

    member = MerchantMember(user_id=USER_ID, merchant_id=MERCHANT_ID, role="member")
    merchant = Merchant(
        id=MERCHANT_ID, name="Acme Stores", slug="acme", status="active", default_currency="KES"
    )

    async def fake_session():
        session = AsyncMock()
        session.exec = AsyncMock(return_value=MagicMock(first=MagicMock(return_value=member)))
        session.get = AsyncMock(return_value=merchant)
        yield session

    from app.core.database import get_session

    app.dependency_overrides[get_human_principal] = fake_principal
    app.dependency_overrides[get_session] = fake_session

    with TestClient(app) as client:
        response = client.get(
            f"/api/v1/auth/merchants/{MERCHANT_ID}",
            headers={"Authorization": "Bearer unused"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["slug"] == "acme"
    assert body["role"] == "member"
    assert body["name"] == "Acme Stores"


def test_merchant_payments_requires_membership() -> None:
    app = FastAPI()
    app.include_router(identity_router)

    async def fake_principal() -> HumanPrincipal:
        return _human()

    async def fake_session():
        session = AsyncMock()
        session.exec = AsyncMock(return_value=MagicMock(first=MagicMock(return_value=None)))
        yield session

    from app.core.database import get_session

    app.dependency_overrides[get_human_principal] = fake_principal
    app.dependency_overrides[get_session] = fake_session

    with TestClient(app) as client:
        response = client.get(
            f"/api/v1/auth/merchants/{MERCHANT_ID}/payments",
            headers={"Authorization": "Bearer unused"},
        )
    assert response.status_code == 403
    assert response.json()["detail"] == "merchant_membership_required"
