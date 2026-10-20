import httpx
import pytest

from app.daraja.c2b import C2BRegistrationUnknown, register_c2b_urls


@pytest.mark.asyncio
async def test_c2b_registration_posts_generated_callback_urls() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path == "/oauth/v1/generate":
            return httpx.Response(200, json={"access_token": "temporary-token"})
        return httpx.Response(200, json={"ResponseCode": "0", "ResponseDescription": "Success"})

    await register_c2b_urls(
        environment="sandbox",
        consumer_key="consumer-key",
        consumer_secret="consumer-secret",
        shortcode="600001",
        validation_url="https://gateway.example.test/cb/c2b/validation/integration-token",
        confirmation_url="https://gateway.example.test/cb/c2b/confirmation/integration-token",
        transport=httpx.MockTransport(handler),
    )

    request = seen[-1]
    assert request.url.path == "/mpesa/c2b/v1/registerurl"
    import json

    body = json.loads(request.content)
    assert body["ShortCode"] == "600001"
    assert body["ResponseType"] == "Completed"
    assert body["ValidationURL"].startswith("https://")
    assert body["ConfirmationURL"].startswith("https://")


@pytest.mark.asyncio
async def test_c2b_server_error_is_not_treated_as_definite_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth/v1/generate":
            return httpx.Response(200, json={"access_token": "temporary-token"})
        return httpx.Response(503, json={"errorMessage": "busy"})

    with pytest.raises(C2BRegistrationUnknown):
        await register_c2b_urls(
            environment="production",
            consumer_key="consumer-key",
            consumer_secret="consumer-secret",
            shortcode="600001",
            validation_url="https://gateway.example.test/cb/c2b/validation/integration-token",
            confirmation_url="https://gateway.example.test/cb/c2b/confirmation/integration-token",
            transport=httpx.MockTransport(handler),
        )
