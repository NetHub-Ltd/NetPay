"""Core-owned encrypted credential storage primitives with key-ID rotation support."""
from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException

from app.core.config import get_settings


def _keyring() -> tuple[str, dict[str, Fernet]]:
    """Load environment-managed Fernet keys; never persist key material with ciphertext."""
    settings = get_settings()
    raw = settings.mpesa_credential_encryption_keys
    if raw is None or not raw.get_secret_value().strip():
        raise HTTPException(status_code=503, detail="credential_encryption_not_configured")
    keys: dict[str, Fernet] = {}
    for item in raw.get_secret_value().split(","):
        key_id, separator, key = item.strip().partition("=")
        if not separator or not key_id or not key:
            raise HTTPException(status_code=503, detail="credential_encryption_keyring_invalid")
        try:
            keys[key_id] = Fernet(key.encode("ascii"))
        except (ValueError, UnicodeEncodeError) as exc:
            raise HTTPException(status_code=503, detail="credential_encryption_keyring_invalid") from exc
    active = settings.mpesa_credential_active_key_id
    if active not in keys:
        raise HTTPException(status_code=503, detail="credential_encryption_active_key_missing")
    return active, keys


def encrypt_credentials(plaintext: bytes) -> bytes:
    """Encrypt credentials using the active key and prefix ciphertext with its key ID."""
    active, keys = _keyring()
    return active.encode("ascii") + b":" + keys[active].encrypt(plaintext)


def decrypt_credentials(ciphertext: bytes) -> bytes:
    """Decrypt with the identified retained key, supporting staged key rotation."""
    try:
        key_id_raw, token = ciphertext.split(b":", 1)
        key_id = key_id_raw.decode("ascii")
        _, keys = _keyring()
        key = keys.get(key_id)
        if key is None:
            raise HTTPException(status_code=503, detail="credential_encryption_key_unavailable")
        return key.decrypt(token)
    except (ValueError, UnicodeDecodeError, InvalidToken) as exc:
        raise HTTPException(status_code=500, detail="stored_credentials_unreadable") from exc
