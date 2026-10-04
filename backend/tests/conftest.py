from __future__ import annotations

import os
from pathlib import Path
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = Path(__file__).resolve().parents[1]
TEST_DB = ROOT / "data" / "test_gateway.db"

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB}"
os.environ["REDIS_REQUIRED"] = "false"
os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "unit-test-signing-key-unused"
os.environ["ADMIN_EMAIL"] = "admin@nethub.test"
os.environ["INTERNAL_API_KEY"] = "unit-test-internal-api-key"
os.environ["NETHUB_API_BASE_URL"] = "http://nethub.test"
os.environ["TEST_USER_PASSWORD"] = "unused"
os.environ["ADMIN_PASSWORD"] = "unused"

# Stable fixture identities (NetHub-shaped)
ADMIN_ID = UUID("00000000-0000-4000-8000-000000000001")
USER_ID = UUID("00000000-0000-4000-8000-000000000002")
TENANT_ID = UUID("00000000-0000-4000-8000-0000000000aa")

from app.core.config import get_settings

get_settings.cache_clear()


@pytest.fixture(scope="session", autouse=True)
def _clean_db():
    if TEST_DB.exists():
        TEST_DB.unlink()
    TEST_DB.parent.mkdir(parents=True, exist_ok=True)
    yield
    if TEST_DB.exists():
        TEST_DB.unlink()


@pytest.fixture
async def client():
    from app.api.deps import get_current_user
    from app.main import app
    from app.schemas.principal import Principal
    from app.services.bootstrap import startup_sequence

    await startup_sequence()

    async def _admin_principal() -> Principal:
        return Principal(
            id=ADMIN_ID,
            email="admin@nethub.test",
            full_name="Admin",
            is_active=True,
            tenant_id=TENANT_ID,
            is_admin=True,
        )

    app.dependency_overrides[get_current_user] = _admin_principal
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def user_client():
    """Client authenticated as a non-admin tenant user."""
    from app.api.deps import get_current_user
    from app.main import app
    from app.schemas.principal import Principal
    from app.services.bootstrap import startup_sequence

    await startup_sequence()

    async def _user_principal() -> Principal:
        return Principal(
            id=USER_ID,
            email="user@nethub.test",
            full_name="User",
            is_active=True,
            tenant_id=TENANT_ID,
            is_admin=False,
        )

    app.dependency_overrides[get_current_user] = _user_principal
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
