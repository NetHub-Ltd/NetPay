"""Unit tests for identity staging probe pure checks (no live network)."""
from __future__ import annotations

from unittest.mock import patch

from app.identity.staging_probe import (
    check_auth_me_unauthorized,
    check_config,
    check_live,
    check_ready,
)


def test_check_live_ok() -> None:
    with patch("app.identity.staging_probe._get", return_value=(200, {"status": "ok"})):
        assert check_live("https://example.test") == []


def test_check_ready_rejects_nethub_fields() -> None:
    with patch(
        "app.identity.staging_probe._get",
        return_value=(200, {"status": "ok", "database": "ok", "nethub": "x"}),
    ):
        errs = check_ready("https://example.test")
        assert any("nethub" in e for e in errs)


def test_check_config_rejects_secrets() -> None:
    with patch(
        "app.identity.staging_probe._get",
        return_value=(
            200,
            {
                "oidc_issuer": "https://auth.example",
                "oidc_client_id": "spa",
                "oidc_redirect_uri": "https://pay.example/auth/callback/",
                "oidc_configured": True,
                "auth_mode": "spa_pkce",
                "client_secret": "leak",
            },
        ),
    ):
        errs = check_config("https://example.test")
        assert any("secret" in e for e in errs)


def test_check_config_ok() -> None:
    with patch(
        "app.identity.staging_probe._get",
        return_value=(
            200,
            {
                "oidc_issuer": "https://auth.example",
                "oidc_client_id": "spa",
                "oidc_redirect_uri": "https://pay.example/auth/callback/",
                "oidc_scopes": "openid profile email",
                "oidc_configured": True,
                "nethub_api_configured": True,
                "auth_mode": "spa_pkce",
            },
        ),
    ):
        assert check_config("https://example.test") == []


def test_auth_me_requires_token() -> None:
    with patch("app.identity.staging_probe._get", return_value=(401, {"detail": "x"})):
        assert check_auth_me_unauthorized("https://example.test") == []
