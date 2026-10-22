"""Security regression tests for authenticated provider-credential encryption."""
import pytest
from cryptography.fernet import Fernet

from app.core.credentials import CredentialEncryptionError, decrypt_credential, encrypt_credential


def test_credential_round_trip_uses_ciphertext() -> None:
    """Ciphertext decrypts with its key and does not contain plaintext."""
    key = Fernet.generate_key().decode("ascii")
    plaintext = "merchant-consumer-secret"
    ciphertext = encrypt_credential(plaintext, key=key)
    assert plaintext.encode() not in ciphertext
    assert decrypt_credential(ciphertext, key=key) == plaintext


def test_credential_decryption_rejects_wrong_key() -> None:
    """A different encryption key cannot decrypt authenticated ciphertext."""
    first_key = Fernet.generate_key().decode("ascii")
    second_key = Fernet.generate_key().decode("ascii")
    ciphertext = encrypt_credential("private-passkey", key=first_key)
    with pytest.raises(CredentialEncryptionError):
        decrypt_credential(ciphertext, key=second_key)


def test_credential_decryption_rejects_tampering() -> None:
    """Tampering with authenticated ciphertext is rejected."""
    key = Fernet.generate_key().decode("ascii")
    ciphertext = encrypt_credential("private-consumer-key", key=key)
    tampered = ciphertext[:-1] + (b"A" if ciphertext[-1:] != b"A" else b"B")
    with pytest.raises(CredentialEncryptionError):
        decrypt_credential(tampered, key=key)


def test_credential_operations_fail_closed_without_key() -> None:
    """Missing key configuration never falls back to plaintext or an ephemeral key."""
    with pytest.raises(CredentialEncryptionError):
        encrypt_credential("must-not-be-plaintext", key="")
