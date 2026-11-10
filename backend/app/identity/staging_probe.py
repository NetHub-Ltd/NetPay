#!/usr/bin/env python3
"""Probe NetPay identity deploy contract against a base URL.

Does not print bearer tokens. Safe default mode is unauthenticated only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any


def _get(url: str, headers: dict[str, str] | None = None, timeout: float = 15.0) -> tuple[int, Any]:
    req = urllib.request.Request(url, headers=headers or {"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                data: Any = json.loads(body) if body else None
            except json.JSONDecodeError:
                data = body
            return resp.status, data
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(body) if body else None
        except json.JSONDecodeError:
            data = body
        return exc.code, data


def check_live(base: str) -> list[str]:
    errors: list[str] = []
    status, data = _get(f"{base}/health/live")
    if status != 200:
        errors.append(f"health/live status={status}")
    elif not isinstance(data, dict) or data.get("status") != "ok":
        errors.append(f"health/live unexpected body={data!r}")
    return errors


def check_ready(base: str) -> list[str]:
    errors: list[str] = []
    status, data = _get(f"{base}/health/ready")
    if status != 200:
        errors.append(f"health/ready status={status}")
        return errors
    if not isinstance(data, dict):
        errors.append("health/ready not json object")
        return errors
    if data.get("status") != "ok" or data.get("database") != "ok":
        errors.append(f"health/ready body={data!r}")
    if "nethub" in data or "oidc" in data:
        errors.append("health/ready must not expose nethub/oidc fields")
    return errors


def check_config(base: str) -> list[str]:
    errors: list[str] = []
    status, data = _get(f"{base}/config.json")
    if status != 200:
        errors.append(f"config.json status={status}")
        return errors
    if not isinstance(data, dict):
        errors.append("config.json not object")
        return errors
    blob = json.dumps(data).lower()
    for forbidden in ("secret", "password", "private_key", "client_secret"):
        if forbidden in blob:
            errors.append(f"config.json must not contain {forbidden}")
    for key in ("oidc_issuer", "oidc_client_id", "oidc_redirect_uri", "oidc_configured", "auth_mode"):
        if key not in data:
            errors.append(f"config.json missing {key}")
    if data.get("auth_mode") != "spa_pkce":
        errors.append(f"auth_mode expected spa_pkce got {data.get('auth_mode')!r}")
    return errors


def check_auth_me(base: str, token: str) -> list[str]:
    errors: list[str] = []
    status, data = _get(
        f"{base}/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    if status != 200:
        errors.append(f"auth/me status={status}")
        return errors
    if not isinstance(data, dict) or "email" not in data or "id" not in data:
        errors.append("auth/me missing id/email")
    return errors


def check_auth_me_unauthorized(base: str) -> list[str]:
    errors: list[str] = []
    status, _ = _get(f"{base}/api/v1/auth/me")
    if status not in (401, 403):
        errors.append(f"auth/me without token expected 401/403 got {status}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NetPay identity staging probe")
    parser.add_argument("--base-url", required=True, help="NetPay origin, no trailing path")
    parser.add_argument(
        "--with-auth",
        action="store_true",
        help="Also call /api/v1/auth/me using NETPAY_PROBE_ACCESS_TOKEN",
    )
    args = parser.parse_args(argv)
    base = args.base_url.rstrip("/")

    all_errors: list[str] = []
    for name, fn in (
        ("live", lambda: check_live(base)),
        ("ready", lambda: check_ready(base)),
        ("config", lambda: check_config(base)),
        ("auth_unauth", lambda: check_auth_me_unauthorized(base)),
    ):
        errs = fn()
        if errs:
            print(f"FAIL {name}: {'; '.join(errs)}")
            all_errors.extend(errs)
        else:
            print(f"PASS {name}")

    if args.with_auth:
        token = (os.environ.get("NETPAY_PROBE_ACCESS_TOKEN") or "").strip()
        if not token:
            print("FAIL auth: NETPAY_PROBE_ACCESS_TOKEN not set")
            all_errors.append("missing NETPAY_PROBE_ACCESS_TOKEN")
        else:
            errs = check_auth_me(base, token)
            if errs:
                print(f"FAIL auth: {'; '.join(errs)}")
                all_errors.extend(errs)
            else:
                print("PASS auth")

    if all_errors:
        print(f"RESULT fail count={len(all_errors)}")
        return 1
    print("RESULT ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
