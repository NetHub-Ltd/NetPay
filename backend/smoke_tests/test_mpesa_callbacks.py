"""Persistence tests for provider callbacks using the CI PostgreSQL database."""
from uuid import uuid4

import pytest
from sqlmodel import select

from app.core.config import Settings
from app.core.database import create_database_engine, create_session_factory
from app.models.integrations import DarajaIntegration
from app.models.merchants import Merchant
from app.models.operations import AuditLog
from app.models.payments import ProviderCallback
from app.mpesa_core.callbacks import record_callback
from app.mpesa_core.errors import UnknownIntegration


def stk_payload(result_code: int = 0) -> dict[str, object]:
    callback: dict[str, object] = {
        "MerchantRequestID": "merchant-request-test",
        "CheckoutRequestID": "checkout-request-test",
        "ResultCode": result_code,
        "ResultDesc": "Test callback",
    }
    if result_code == 0:
        callback["CallbackMetadata"] = {
            "Item": [
                {"Name": "Amount", "Value": 10},
                {"Name": "MpesaReceiptNumber", "Value": "QAB123XYZ"},
                {"Name": "PhoneNumber", "Value": "254712345678"},
            ]
        }
    return {"Body": {"stkCallback": callback}}


@pytest.mark.asyncio
async def test_callbacks_are_durable_idempotent_and_conflicts_are_audited():
    engine = create_database_engine(Settings(environment="test"))
    factory = create_session_factory(engine)
    merchant = Merchant(name="Callback test merchant", slug=f"callback-test-{uuid4().hex}")
    integration = None
    try:
        async with factory() as session:
            session.add(merchant)
            await session.commit()
            await session.refresh(merchant)
            integration = DarajaIntegration(
                merchant_id=merchant.id,
                environment="sandbox",
                status="active",
                credential_status="valid",
                shortcode="174379",
                c2b_enabled=True,
                enabled_capabilities=["stk_push", "c2b_validation"],
            )
            session.add(integration)
            await session.commit()
            await session.refresh(integration)

        first = await record_callback(factory, integration.integration_id, "stk", stk_payload())
        duplicate = await record_callback(factory, integration.integration_id, "stk", stk_payload())
        conflict = await record_callback(factory, integration.integration_id, "stk", stk_payload(result_code=1))
        assert first.status == "recorded"
        assert duplicate.status == "duplicate"
        assert conflict.status == "conflict"

        accepted = await record_callback(
            factory,
            integration.integration_id,
            "c2b_validation",
            {
                "TransID": "TX-C2B-1",
                "TransAmount": "10.00",
                "BusinessShortCode": "174379",
                "BillRefNumber": "INV-1",
                "MSISDN": "254712345678",
            },
        )
        assert accepted.validation_accepted is True
        confirmation = await record_callback(
            factory,
            integration.integration_id,
            "c2b_confirmation",
            {
                "TransID": "TX-C2B-1",
                "TransAmount": "10.00",
                "BusinessShortCode": "174379",
                "BillRefNumber": "INV-1",
                "MSISDN": "254712345678",
            },
        )
        assert confirmation.status == "recorded"
        rejected = await record_callback(
            factory,
            integration.integration_id,
            "c2b_validation",
            {
                "TransID": "TX-C2B-2",
                "TransAmount": "10.00",
                "BusinessShortCode": "999999",
                "BillRefNumber": "INV-2",
            },
        )
        assert rejected.validation_accepted is False
        with pytest.raises(UnknownIntegration):
            await record_callback(factory, "int_missing", "stk", stk_payload())
    finally:
        async with factory() as session:
            if integration is not None:
                callbacks = await session.exec(
                    select(ProviderCallback).where(ProviderCallback.integration_id == integration.id)
                )
                for row in callbacks.all():
                    await session.delete(row)
                audits = await session.exec(
                    select(AuditLog).where(AuditLog.merchant_id == merchant.id)
                )
                for row in audits.all():
                    await session.delete(row)
                stored_integration = await session.get(DarajaIntegration, integration.id)
                if stored_integration is not None:
                    await session.delete(stored_integration)
            stored_merchant = await session.get(Merchant, merchant.id)
            if stored_merchant is not None:
                await session.delete(stored_merchant)
            await session.commit()
        await engine.dispose()
