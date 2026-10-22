"""Authenticated encryption for merchant-owned provider credentials.

The encryption key is supplied by deployment configuration and stored separately
from PostgreSQL. No default or ephemeral key is generated: losing the configured
key must not silently make existing credentials unreadable.
"""
from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken
from pydantic import SecretStr

from app.core.config import get_settings


class CredentialEncryptionError(RuntimeError):
    """Raised when provider credential encryption/decryption cannot be done safely."""


def _fernet(key: SecretStr | str | None = None) -> Fernet:
    """Build Fernet from an explicit key or the deployment-provided setting."""
    configured = key if key is not None else get_settings().credential_encryption_key
    raw_key = configured.get_secret_value() if isinstance(configured, SecretStr) else configured
    if not raw_key:
        raise CredentialEncryptionError("CREDENTIAL_ENCRYPTION_KEY is required for provider credentials")
    try:
        return Fernet(raw_key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise CredentialEncryptionError("CREDENTIAL_ENCRYPTION_KEY is invalid") from exc


def encrypt_credential(value: str, *, key: SecretStr | str | None = None) -> bytes:
    """Encrypt a non-empty provider credential and return authenticated ciphertext."""
    if not value:
        raise ValueError("Provider credential must not be empty")
    return _fernet(key).encrypt(value.encode("utf-8"))


def decrypt_credential(ciphertext: bytes, *, key: SecretStr | str | None = None) -> str:
    """Decrypt ciphertext while keeping low-level cryptographic errors private."""
    try:
        return _fernet(key).decrypt(ciphertext).decode("utf-8")
    except InvalidToken as exc:
        raise CredentialEncryptionError("Provider credential ciphertext could not be authenticated") from exc
    except UnicodeDecodeError as exc:
        raise CredentialEncryptionError("Provider credential plaintext is not valid UTF-8") from exc
