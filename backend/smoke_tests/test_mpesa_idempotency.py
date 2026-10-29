"""Database-backed guardrail for provider-operation idempotency keys.

Idempotency policy belongs to NetPay's application layer, not mpesa_core.
This test verifies the durable uniqueness constraint that prevents duplicate
provider-operation rows for the same integration, operation and idempotency key.
"""
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.core.config import Settings
from app.core.database import create_database_engine, create_session_factory
from app.models.integrations import DarajaIntegration
from app.models.merchants import Merchant
from app.models.operations import ProviderRequest


@pytest.mark.asyncio
async def test_provider_request_idempotency_key_is_unique_per_integration_operation() -> None:
    settings = Settings(environment="test")
    engine = create_database_engine(settings)
    factory = create_session_factory(engine)
    merchant = Merchant(name="Idempotency test merchant", slug=f"mpesa-idem-{uuid4().hex}")
    integration_id = None
    merchant_id = None
    try:
        async with factory() as session:
            session.add(merchant)
            await session.commit()
            await session.refresh(merchant)
            merchant_id = merchant.id
            integration = DarajaIntegration(
                merchant_id=merchant.id,
                environment="sandbox",
                status="pending",
                credential_status="pending",
                shortcode="174379",
                product_type="paybill",
                enabled_capabilities=["stk_push"],
            )
            session.add(integration)
            await session.commit()
            await session.refresh(integration)
            integration_id = integration.id

            first = ProviderRequest(
                merchant_id=merchant.id,
                integration_id=integration.id,
                operation="stk_push",
                idempotency_key="merchant-payment-key-1",
                request_hash="a" * 64,
                outcome="started",
            )
            session.add(first)
            await session.commit()

            duplicate = ProviderRequest(
                merchant_id=merchant.id,
                integration_id=integration.id,
                operation="stk_push",
                idempotency_key="merchant-payment-key-1",
                request_hash="b" * 64,
                outcome="started",
            )
            session.add(duplicate)
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()

            distinct_operation = ProviderRequest(
                merchant_id=merchant_id,
                integration_id=integration_id,
                operation="transaction_status",
                idempotency_key="merchant-payment-key-1",
                request_hash="b" * 64,
                outcome="started",
            )
            session.add(distinct_operation)
            await session.commit()
    finally:
        async with factory() as session:
            if integration_id is not None:
                rows = await session.exec(
                    select(ProviderRequest).where(ProviderRequest.integration_id == integration_id)
                )
                for row in rows.all():
                    await session.delete(row)
                stored_integration = await session.get(DarajaIntegration, integration_id)
                if stored_integration is not None:
                    await session.delete(stored_integration)
            stored_merchant = await session.get(Merchant, merchant_id) if merchant_id is not None else None
            if stored_merchant is not None:
                await session.delete(stored_merchant)
            await session.commit()
        await engine.dispose()
