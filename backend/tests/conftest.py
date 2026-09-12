from __future__ import annotations

import os
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = Path(__file__).resolve().parents[1]
TEST_DB = ROOT / "data" / "test_gateway.db"

# Fixture-only values — not production secrets. Single source for all tests.
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB}"
os.environ["REDIS_REQUIRED"] = "false"
os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "unit-test-signing-key-for-jwt-only"
os.environ["ADMIN_EMAIL"] = "admin@nethub.test"
os.environ["ADMIN_PASSWORD"] = "unit-test-admin-password"
os.environ["INTERNAL_API_KEY"] = "unit-test-internal-api-key"
# Shared password for seeded non-admin users in tests
os.environ["TEST_USER_PASSWORD"] = "unit-test-user-password"

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
    from app.main import app
    from app.services.bootstrap import startup_sequence

    await startup_sequence()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
