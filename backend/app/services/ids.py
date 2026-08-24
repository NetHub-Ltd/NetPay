from __future__ import annotations
import secrets
import string

def new_id(prefix: str) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return f"{prefix}_{''.join(secrets.choice(alphabet) for _ in range(16))}"

def new_client_id() -> str:
    return new_id("cli")

def new_client_secret() -> str:
    return secrets.token_urlsafe(32)
