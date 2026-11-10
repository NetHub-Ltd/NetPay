"""Unit tests for the independent frontend/BFF staging probe."""
from __future__ import annotations

from unittest.mock import patch

from app.identity.staging_probe import (
    check_api_boundaries,
    check_api_health,
    check_frontend_bff,
    check_frontend_login,
    check_frontend_ready,
    check_frontend_status,
)


def test_api_health_passes() -> None:
    with patch(
        "app.identity.staging_probe._get",
        side_effect=[
            (200, {"status": "ok"}, "https://api.example/health/live"),
            (200, {"status": "ok", "database": "ok"}, "https://api.example/health/ready"),
        ],
    ):
        assert check_api_health("https://api.example") == []


def test_api_boundaries_reject_direct_and_internal_access() -> None:
    with patch(
        "app.identity.staging_probe._get",
        side_effect=[
            (401, {"detail": "bearer_token_required"}, ""),
            (401, {"detail": "bff_internal_auth_required"}, ""),
            (404, {"detail": "Not Found"}, ""),
        ],
    ):
        assert check_api_boundaries("https://api.example") == []


def test_frontend_status_requires_oidc_and_bff_without_secrets() -> None:
    with patch(
        "app.identity.staging_probe._get",
        return_value=(200, {"oidc_configured": True, "bff_configured": True}, ""),
    ):
        from app.identity.staging_probe import check_frontend_status
        assert check_frontend_status("https://pay.example") == []


def test_frontend_status_rejects_secret_fields() -> None:
    with patch(
        "app.identity.staging_probe._get",
        return_value=(200, {"oidc_configured": True, "bff_configured": True, "client_secret": "leak"}, ""),
    ):
        assert "Frontend auth status exposed sensitive configuration" in check_frontend_status("https://pay.example")


def test_frontend_login_and_protected_dashboard() -> None:
    with patch(
        "app.identity.staging_probe._get",
        side_effect=[
            (200, "<html>Continue with NetHub</html>", "https://pay.example/login/"),
            (200, "<html>Login</html>", "https://pay.example/login/"),
        ],
    ):
        assert check_frontend_login("https://pay.example") == []
        assert check_frontend_bff("https://pay.example") == [
            "BFF must reject unauthenticated browser API requests"
        ]

def test_frontend_readiness_requires_oidc_api_and_session_store() -> None:
    with patch(
        "app.identity.staging_probe._get",
        return_value=(200, {"status": "ok", "oidc_configured": True, "bff_configured": True}, ""),
    ):
        assert check_frontend_ready("https://pay.example") == []
