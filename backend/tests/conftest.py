"""Database setup for integration tests; refuses to touch non-test databases."""

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlmodel import SQLModel

from app.config import get_settings
from app import models  # noqa: F401


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database() -> None:
    settings = get_settings()
    if settings.environment != "test":
        return
    if not settings.database_url.startswith("sqlite+aiosqlite:///"):
        raise RuntimeError("Tests require a dedicated SQLite DATABASE_URL; refusing to drop a non-test database")

    sync_url = settings.database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    db_path = sync_url.removeprefix("sqlite:///")
    if db_path and db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(sync_url)
    try:
        SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)
    finally:
        engine.dispose()
