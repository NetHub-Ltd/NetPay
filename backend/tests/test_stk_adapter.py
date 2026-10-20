import httpx
import pytest

from app.daraja.stk import STKOutcomeUnknown, initiate_stk_push


@pytest.mark.asyncio
async def test_stk_uses_product_type_amount_and_hosted_callback() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path == "/oauth/v1/generate":
            return httpx.Response(200, json={"access_token": "temporary-token"})
        assert request.url.path == "/mpesa/stkpush/v1/processrequest"
        return httpx.Response(200, json={
            "ResponseCode": "0",
            "MerchantRequestID": "merchant-request-1",
            "CheckoutRequestID": "checkout-request-1",
            "ResponseDescription": "Request accepted for processing",
        })

    result = await initiate_stk_push(
        environment="sandbox",
        consumer_key="consumer-key",
        consumer_secret="consumer-secret",
        passkey="passkey",
        business_shortcode="174379",
        party_b_shortcode="174379",
        product_type="paybill",
        amount_kes=25,
        phone_number="254712345678",
        callback_url="https://gateway.example.test/cb/stk/integration-token",
        account_reference="REFERENCE123456",
        description="Test payment",
        transport=httpx.MockTransport(handler),
    )

    assert result.checkout_request_id == "checkout-request-1"
    request = seen[-1]
    import json

    body = json.loads(request.content)
    assert body["Amount"] == 25
    assert body["TransactionType"] == "CustomerPayBillOnline"
    assert body["CallBackURL"].startswith("https://gateway.example.test/cb/stk/")
    assert body["AccountReference"] == "REFERENCE123"
    assert body["PartyA"] == "254712345678"


@pytest.mark.asyncio
async def test_stk_server_error_is_an_ambiguous_outcome() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth/v1/generate":
            return httpx.Response(200, json={"access_token": "temporary-token"})
        return httpx.Response(503, json={"errorMessage": "busy"})

    with pytest.raises(STKOutcomeUnknown):
        await initiate_stk_push(
            environment="sandbox",
            consumer_key="consumer-key",
            consumer_secret="consumer-secret",
            passkey="passkey",
            business_shortcode="174379",
            party_b_shortcode="174379",
            product_type="paybill",
            amount_kes=25,
            phone_number="254712345678",
            callback_url="https://gateway.example.test/cb/stk/integration-token",
            account_reference="REFERENCE123",
            description="Test payment",
            transport=httpx.MockTransport(handler),
        )
