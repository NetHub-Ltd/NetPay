"""Public SPA config must not expose secrets."""
from app.core.config import get_settings
from app.identity.spa_config import public_spa_config


def test_public_spa_config_shape(monkeypatch) -> None:
    monkeypatch.setenv("OIDC_ISSUER", "https://auth.example.com")
    monkeypatch.setenv("OIDC_CLIENT_ID", "spa-client")
    monkeypatch.setenv("OIDC_REDIRECT_URI", "https://pay.example.com/auth/callback/")
    monkeypatch.setenv("NETHUB_API_BASE_URL", "https://api.example.com")
    get_settings.cache_clear()
    body = public_spa_config()
    assert body["oidc_configured"] is True
    assert body["oidc_client_id"] == "spa-client"
    assert body["nethub_api_configured"] is True
    assert body["auth_mode"] == "spa_pkce"
    assert "secret" not in str(body).lower()
    get_settings.cache_clear()


def test_public_spa_config_unconfigured(monkeypatch) -> None:
    monkeypatch.setenv("OIDC_ISSUER", "")
    monkeypatch.setenv("OIDC_CLIENT_ID", "")
    monkeypatch.setenv("OIDC_REDIRECT_URI", "")
    monkeypatch.delenv("NETHUB_API_BASE_URL", raising=False)
    get_settings.cache_clear()
    body = public_spa_config()
    assert body["oidc_configured"] is False
    get_settings.cache_clear()
