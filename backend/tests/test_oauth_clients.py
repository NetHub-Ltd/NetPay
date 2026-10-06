"""OAuth client create/list and client_credentials token."""
from __future__ import annotations

from uuid import uuid4

import pytest


async def _seed_tenant():
    from tests.conftest import ADMIN_ID
    from app.core.db import AsyncSessionLocal
    from app.crud.tenant import tenant_crud

    tenant_id = uuid4()
    async with AsyncSessionLocal() as session:
        await tenant_crud.create_tenant(
            session,
            name="OAuth Test Biz",
            slug=f"oauth-test-{tenant_id.hex[:8]}",
            created_by=ADMIN_ID,
            id=tenant_id,
            status="active",
        )
        await session.commit()
    return tenant_id


def _drop_auth_override():
    from app.main import app
    from app.api.deps import get_current_user

    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_create_and_list_oauth_client(client):
    tenant_id = await _seed_tenant()

    create = await client.post(
        "/v1/oauth/clients",
        json={"tenant_id": str(tenant_id), "name": "Test client"},
    )
    assert create.status_code == 201, create.text
    body = create.json()
    assert body.get("client_id", "").startswith("cli_")
    assert body.get("client_secret")
    assert body["name"] == "Test client"

    listed = await client.get(f"/v1/oauth/clients?tenant_id={tenant_id}")
    assert listed.status_code == 200, listed.text
    rows = listed.json()
    assert any(r["client_id"] == body["client_id"] for r in rows)
    assert all("client_secret" not in r for r in rows)


@pytest.mark.asyncio
async def test_oauth_client_non_admin_forbidden(user_client):
    res = await user_client.post(
        "/v1/oauth/clients",
        json={"tenant_id": "00000000-0000-4000-8000-0000000000aa", "name": "Nope"},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_client_credentials_token(client):
    tenant_id = await _seed_tenant()
    created = await client.post(
        "/v1/oauth/clients",
        json={"tenant_id": str(tenant_id), "name": "M2M client"},
    )
    assert created.status_code == 201, created.text
    cid = created.json()["client_id"]
    secret = created.json()["client_secret"]

    _drop_auth_override()

    tok = await client.post(
        "/v1/oauth/token",
        json={"grant_type": "client_credentials", "client_id": cid, "client_secret": secret},
    )
    assert tok.status_code == 200, tok.text
    body = tok.json()
    assert body.get("access_token")
    assert body.get("token_type") == "bearer"
    assert body.get("client_id") == cid
    assert body.get("tenant_id") == str(tenant_id)

    headers = {"Authorization": f"Bearer {body['access_token']}"}
    listed = await client.get(f"/v1/oauth/clients?tenant_id={tenant_id}", headers=headers)
    assert listed.status_code == 403

    bad = await client.post(
        "/v1/oauth/token",
        json={"grant_type": "client_credentials", "client_id": cid, "client_secret": "wrong-secret-value"},
    )
    assert bad.status_code == 401


@pytest.mark.asyncio
async def test_machine_token_lists_payments(client):
    tenant_id = await _seed_tenant()
    created = await client.post(
        "/v1/oauth/clients",
        json={"tenant_id": str(tenant_id), "name": "Pay client"},
    )
    assert created.status_code == 201, created.text

    _drop_auth_override()

    tok = await client.post(
        "/v1/oauth/token",
        json={
            "grant_type": "client_credentials",
            "client_id": created.json()["client_id"],
            "client_secret": created.json()["client_secret"],
        },
    )
    assert tok.status_code == 200, tok.text
    headers = {"Authorization": f"Bearer {tok.json()['access_token']}"}
    res = await client.get(f"/v1/payment-intents?tenant_id={tenant_id}", headers=headers)
    assert res.status_code == 200, res.text
    assert isinstance(res.json(), list)
