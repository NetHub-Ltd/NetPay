"""OAuth client create/list (admin machine credentials)."""
from __future__ import annotations

from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_create_and_list_oauth_client(client):
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
