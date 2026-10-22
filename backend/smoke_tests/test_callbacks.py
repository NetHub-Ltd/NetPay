"""Public callback intake tests for deduplication and untrusted evidence."""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.callbacks import receive_stk_callback
from app.models.integrations import DarajaIntegration
from app.models.payments import Payment, ProviderCallback


def _result(value: object) -> MagicMock:
    result = MagicMock()
    result.first.return_value = value
    return result


def _callback() -> dict[str, object]:
    return {
        "Body": {
            "stkCallback": {
                "MerchantRequestID": "merchant-request-123",
                "CheckoutRequestID": "ws_CO_checkout-123",
                "ResultCode": 0,
                "ResultDesc": "Sensitive free-text must not be persisted",
                "CallbackMetadata": {
                    "Item": [
                        {"Name": "Amount", "Value": 100.0},
                        {"Name": "MpesaReceiptNumber", "Value": "ABC123"},
                        {"Name": "TransactionDate", "Value": 20261022123045},
                        {"Name": "PhoneNumber", "Value": 254712345678},
                        {"Name": "Balance", "Value": 999999},
                    ]
                },
            }
        }
    }


@pytest.mark.asyncio
async def test_success_callback_is_stored_as_untrusted_evidence_not_paid_state() -> None:
    """A callback with ResultCode zero cannot directly mark a payment succeeded."""
    merchant_id = uuid4()
    integration = DarajaIntegration(
        merchant_id=merchant_id,
        integration_id="int_callback",
        environment="sandbox",
        status="active",
    )
    payment = Payment(
        merchant_id=merchant_id,
        integration_id=integration.id,
        merchant_reference="order-1",
        amount_minor=10_000,
        status="pending",
        provider_checkout_request_id="ws_CO_checkout-123",
        provider_merchant_request_id="merchant-request-123",
    )
    session = MagicMock()
    session.exec = AsyncMock(side_effect=[_result(integration), _result(None), _result(payment)])
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    ack = await receive_stk_callback("int_callback", _callback(), session)

    record = next(call.args[0] for call in session.add.call_args_list if isinstance(call.args[0], ProviderCallback))
    assert ack.ResultCode == 0
    assert payment.status == "unknown"
    assert record.processing_status == "verification_required"
    assert record.payment_id == payment.id
    assert record.payload["result_code"] == 0
    assert record.payload["receipt"] == "ABC123"
    assert "phone_number" not in record.payload
    assert "ResultDesc" not in record.payload
    assert "Balance" not in record.payload
    assert "PhoneNumber" not in record.payload
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_duplicate_callback_is_acknowledged_without_reapplying_state() -> None:
    """A repeated provider event is deduplicated before payment lookup or mutation."""
    integration = DarajaIntegration(
        merchant_id=uuid4(),
        integration_id="int_callback",
        environment="sandbox",
        status="active",
    )
    existing = ProviderCallback(
        integration_id=integration.id,
        provider_event_id="ws_CO_checkout-123",
        dedupe_fingerprint="f" * 64,
        payload={},
    )
    session = MagicMock()
    session.exec = AsyncMock(side_effect=[_result(integration), _result(existing)])
    session.add = MagicMock()
    session.commit = AsyncMock()

    ack = await receive_stk_callback("int_callback", _callback(), session)
    assert ack.ResultCode == 0
    session.add.assert_not_called()
    session.commit.assert_not_awaited()
    assert session.exec.await_count == 2


@pytest.mark.asyncio
async def test_unmatched_callback_is_persisted_without_changing_payment() -> None:
    """Callbacks that do not match a known checkout request remain unmatched evidence."""
    integration = DarajaIntegration(
        merchant_id=uuid4(),
        integration_id="int_callback",
        environment="sandbox",
        status="active",
    )
    session = MagicMock()
    session.exec = AsyncMock(side_effect=[_result(integration), _result(None), _result(None)])
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()

    ack = await receive_stk_callback("int_callback", _callback(), session)
    record = next(call.args[0] for call in session.add.call_args_list if isinstance(call.args[0], ProviderCallback))
    assert ack.ResultCode == 0
    assert record.processing_status == "unmatched"
    assert record.payment_id is None
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_unknown_integration_callback_is_rejected() -> None:
    """An opaque integration ID is routing only and must resolve to a stored integration."""
    session = MagicMock()
    session.exec = AsyncMock(return_value=_result(None))
    with pytest.raises(HTTPException) as error:
        await receive_stk_callback("int_missing", _callback(), session)
    assert error.value.status_code == 404
