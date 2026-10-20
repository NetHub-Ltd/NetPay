"""Authenticated encryption for merchant-owned provider credentials.

The encryption key is configuration, never stored beside ciphertext. Callers
must avoid logging plaintext, ciphertext, or exception payloads.
"""

from cryptography.fernet import Fernet, InvalidToken

from app.config import Settings, get_settings


class CredentialEncryptionError(RuntimeError):
    """Raised when configured credential encryption cannot be used safely."""


def _fernet(settings: Settings | None = None) -> Fernet:
    configured = (settings or get_settings()).credential_encryption_key
    if configured is None:
        raise CredentialEncryptionError("Credential encryption is not configured")
    try:
        return Fernet(configured.get_secret_value().encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise CredentialEncryptionError("Credential encryption key is invalid") from exc


def encrypt_secret(value: str, settings: Settings | None = None) -> bytes:
    if not value:
        raise ValueError("Credential value must not be empty")
    return _fernet(settings).encrypt(value.encode("utf-8"))


def decrypt_secret(ciphertext: bytes, settings: Settings | None = None) -> str:
    try:
        plaintext = _fernet(settings).decrypt(ciphertext)
    except InvalidToken as exc:
        raise CredentialEncryptionError("Credential ciphertext could not be authenticated") from exc
    return plaintext.decode("utf-8")
