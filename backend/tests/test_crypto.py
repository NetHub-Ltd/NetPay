import pytest
from pydantic import SecretStr

from app.config import Settings
from app.crypto import CredentialEncryptionError, decrypt_secret, encrypt_secret


TEST_KEY = "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="


def test_credentials_round_trip_without_plaintext_storage() -> None:
    settings = Settings(credential_encryption_key=SecretStr(TEST_KEY))

    ciphertext = encrypt_secret("daraja-consumer-secret", settings)

    assert b"daraja-consumer-secret" not in ciphertext
    assert decrypt_secret(ciphertext, settings) == "daraja-consumer-secret"


def test_tampered_ciphertext_is_rejected() -> None:
    settings = Settings(credential_encryption_key=SecretStr(TEST_KEY))
    ciphertext = encrypt_secret("sensitive-value", settings)
    tampered = ciphertext[:-1] + (b"A" if ciphertext[-1:] != b"A" else b"B")

    with pytest.raises(CredentialEncryptionError):
        decrypt_secret(tampered, settings)


def test_missing_key_fails_closed() -> None:
    settings = Settings(credential_encryption_key=None)

    with pytest.raises(CredentialEncryptionError):
        encrypt_secret("sensitive-value", settings)
