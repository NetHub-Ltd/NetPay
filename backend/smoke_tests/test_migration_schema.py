"""Integration checks for the applied Alembic schema."""

import asyncio
import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings


EXPECTED_TABLES = {
    "merchant",
    "providerintegration",
    "m2mclient",
    "payment",
    "paymentattempt",
    "idempotencyrecord",
    "paymentverification",
    "providerrequest",
    "providercallback",
    "reconciliationrun",
    "reconciliationitem",
    "eventoutbox",
    "webhookendpoint",
    "eventdelivery",
    "eventdeliveryattempt",
    "auditevent",
}


@pytest.mark.asyncio
async def test_alembic_head_contains_all_sixteen_domain_tables() -> None:
    """CI verifies the real PostgreSQL schema after `alembic upgrade head`."""
    database_url = get_settings().async_database_url()
    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))
            assert EXPECTED_TABLES.issubset(tables)
            revision = await connection.execute(text("SELECT version_num FROM alembic_version"))
            assert revision.scalar_one() == "0002_full_domain_schema"

            for table_name in EXPECTED_TABLES:
                columns = await connection.run_sync(
                    lambda sync, name=table_name: {column["name"] for column in inspect(sync).get_columns(name)}
                )
                assert {"id", "created_at", "updated_at", "deleted_at"}.issubset(columns), table_name
    finally:
        await engine.dispose()
