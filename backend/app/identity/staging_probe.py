#!/usr/bin/env python3
"""Probe the independent NetPay API and Next.js BFF staging contract."""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse


def _get(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float = 15.0,
) -> tuple[int, Any, str]:
    request = urllib.request.Request(url, headers=headers or {"Accept": "application/json"})
    opener = urllib.request.build_opener()
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            try:
                data: Any = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                data = raw
            return response.status, data, response.geturl()
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            data = raw
        return exc.code, data, exc.geturl()


def check_api_health(api: str) -> list[str]:
    errors: list[str] = []
    status, data, _ = _get(api + "/health/live")
    if status != 200 or not isinstance(data, dict) or data.get("status") != "ok":
        errors.append("API health/live failed")
    status, data, _ = _get(api + "/health/ready")
    if status != 200 or not isinstance(data, dict) or data.get("status") != "ok" or data.get("database") != "ok":
        errors.append("API health/ready failed")
    return errors


def check_api_boundaries(api: str) -> list[str]:
    errors: list[str] = []
    status, _, _ = _get(api + "/api/v1/auth/me")
    if status not in (401, 403):
        errors.append("Direct API human endpoint must reject unauthenticated requests")
    status, _, _ = _get(api + "/internal/v1/bff/sessions/" + ("a" * 64))
    if status != 401:
        errors.append("Internal BFF session endpoint must reject requests without the service secret")
    status, _, _ = _get(api + "/config.json")
    if status != 404:
        errors.append("Backend must not expose the former public SPA config endpoint")
    return errors


def check_frontend_status(frontend: str) -> list[str]:
    status, data, _ = _get(frontend + "/api/auth/status")
    if status != 200 or not isinstance(data, dict):
        return ["Frontend auth status endpoint failed"]
    errors: list[str] = []
    if data.get("oidc_configured") is not True:
        errors.append("Frontend OIDC configuration is incomplete")
    if data.get("bff_configured") is not True:
        errors.append("Frontend BFF configuration is incomplete")
    forbidden = ("client_secret", "access_token", "refresh_token", "private_key", "password")
    serialized = json.dumps(data).lower()
    if any(key in serialized for key in forbidden):
        errors.append("Frontend auth status exposed sensitive configuration")
    return errors


def check_frontend_ready(frontend: str) -> list[str]:
    status, data, _ = _get(frontend + "/api/health/ready")
    if status != 200 or not isinstance(data, dict) or data.get("status") != "ok":
        return ["Frontend readiness failed (OIDC, API or BFF session store not ready)"]
    return []


def check_frontend_login(frontend: str) -> list[str]:
    status, body, _ = _get(frontend + "/login/")
    if status != 200 or not isinstance(body, str) or "Continue with NetHub" not in body:
        return ["Frontend login page did not render"]
    return []


def check_frontend_bff(frontend: str) -> list[str]:
    errors: list[str] = []
    status, _, _ = _get(frontend + "/api/backend/v1/auth/me")
    if status != 401:
        errors.append("BFF must reject unauthenticated browser API requests")
    status, _, final_url = _get(frontend + "/dashboard/")
    if status != 200 or urlparse(final_url).path.rstrip("/") != "/login":
        errors.append("Dashboard must redirect unauthenticated visitors to login")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NetPay independent frontend/BFF staging probe")
    parser.add_argument("--base-url", required=True, help="FastAPI API origin")
    parser.add_argument("--frontend-url", required=True, help="Next.js public origin")
    args = parser.parse_args(argv)
    api = args.base_url.rstrip("/")
    frontend = args.frontend_url.rstrip("/")

    checks = (
        ("api_health", lambda: check_api_health(api)),
        ("api_boundaries", lambda: check_api_boundaries(api)),
        ("frontend_status", lambda: check_frontend_status(frontend)),
        ("frontend_ready", lambda: check_frontend_ready(frontend)),
        ("frontend_login", lambda: check_frontend_login(frontend)),
        ("frontend_bff", lambda: check_frontend_bff(frontend)),
    )
    failures: list[str] = []
    for name, check in checks:
        errors = check()
        if errors:
            print("FAIL " + name + ": " + "; ".join(errors))
            failures.extend(errors)
        else:
            print("PASS " + name)
    if failures:
        print("RESULT fail count=" + str(len(failures)))
        return 1
    print("RESULT ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
