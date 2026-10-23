"""Database-backed provider-operation idempotency tests."""
import asyncio
from uuid import uuid4

import httpx
import pytest
from cryptography.fernet import Fernet
from sqlmodel import select

from app.core.config import Settings
from app.core.database import create_database_engine, create_session_factory
from app.models.integrations import DarajaIntegration
from app.models.merchants import Merchant
from app.models.operations import ProviderRequest
from app.mpesa_core.client import MpesaCore
from app.mpesa_core.credentials import CredentialVault
from app.mpesa_core.errors import IdempotencyConflictError
from app.mpesa_core.schemas import OperationOutcome, STKPushRequest


@pytest.mark.asyncio
async def test_concurrent_stk_replay_sends_once_and_changed_payload_conflicts():
    settings = Settings(
        environment="test",
        mpesa_credential_encryption_keys=f"v1={Fernet.generate_key().decode('ascii')}",
        mpesa_credential_active_key_id="v1",
        mpesa_public_base_url="https://pay.example.test",
    )
    engine = create_database_engine(settings)
    factory = create_session_factory(engine)
    merchant = Merchant(name="Idempotency test merchant", slug=f"mpesa-idem-{uuid4().hex}")
    integration = None
    stk_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal stk_calls
        if request.url.path == "/oauth/v1/generate":
            return httpx.Response(200, json={"access_token": "test-token", "expires_in": 3600})
        if request.url.path == "/mpesa/stkpush/v1/processrequest":
            stk_calls += 1
            return httpx.Response(200, json={
                "ResponseCode": "0",
                "MerchantRequestID": "merchant-request-idem",
                "CheckoutRequestID": "checkout-request-idem",
            })
        return httpx.Response(404, json={"errorMessage": "unexpected endpoint"})

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    core = None
    try:
        async with factory() as session:
            session.add(merchant)
            await session.commit()
            await session.refresh(merchant)
            integration = DarajaIntegration(
                merchant_id=merchant.id,
                environment="sandbox",
                status="pending",
                credential_status="pending",
                shortcode="174379",
                party_b_shortcode="174379",
                product_type="paybill",
                enabled_capabilities=["stk_push"],
            )
            CredentialVault(settings).store(
                integration,
                consumer_key="consumer-key",
                consumer_secret="consumer-secret",
                passkey="passkey",
            )
            integration.status = "active"
            integration.credential_status = "valid"
            integration.stk_callback_url = f"https://pay.example.test/callbacks/mpesa/stk/{integration.integration_id}"
            integration.c2b_validation_url = f"https://pay.example.test/callbacks/mpesa/c2b/validation/{integration.integration_id}"
            integration.c2b_confirmation_url = f"https://pay.example.test/callbacks/mpesa/c2b/confirmation/{integration.integration_id}"
            session.add(integration)
            await session.commit()
            await session.refresh(integration)

        core = MpesaCore(settings, session_factory=factory, http_client=http)
        request = STKPushRequest(
            phone_number="254712345678",
            amount_minor=1000,
            account_reference="ORDER-1",
            description="NetPay order",
        )
        results = await asyncio.gather(
            core.stk_push(integration, request, idempotency_key="merchant-payment-key-1"),
            core.stk_push(integration, request, idempotency_key="merchant-payment-key-1"),
        )
        assert stk_calls == 1
        assert any(result.outcome is OperationOutcome.ACCEPTED for result in results)
        assert all(result.outcome in {OperationOutcome.ACCEPTED, OperationOutcome.UNKNOWN} for result in results)

        changed_request = STKPushRequest(
            phone_number="254712345678",
            amount_minor=2000,
            account_reference="ORDER-1",
            description="NetPay order",
        )
        with pytest.raises(IdempotencyConflictError):
            await core.stk_push(
                integration,
                changed_request,
                idempotency_key="merchant-payment-key-1",
            )
        assert stk_calls == 1
    finally:
        if core is not None:
            await core.aclose()
        await http.aclose()
        async with factory() as session:
            if integration is not None:
                provider_requests = await session.exec(
                    select(ProviderRequest).where(ProviderRequest.integration_id == integration.id)
                )
                for row in provider_requests.all():
                    await session.delete(row)
                stored_integration = await session.get(DarajaIntegration, integration.id)
                if stored_integration is not None:
                    await session.delete(stored_integration)
            stored_merchant = await session.get(Merchant, merchant.id)
            if stored_merchant is not None:
                await session.delete(stored_merchant)
            await session.commit()
        await engine.dispose()
