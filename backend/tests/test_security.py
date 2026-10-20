from uuid import uuid4

from app.security import (
    create_access_token,
    decode_access_token,
    hash_client_secret,
    verify_client_secret,
)


SECRET = "test-client-secret-that-is-at-least-32-characters-long"


def test_client_secret_hash_verifies_only_matching_secret() -> None:
    encoded = hash_client_secret(SECRET)

    assert encoded.startswith("scrypt$")
    assert SECRET not in encoded
    assert verify_client_secret(SECRET, encoded)
    assert not verify_client_secret("different-client-secret-value-long-enough", encoded)


def test_malformed_secret_hash_fails_closed() -> None:
    assert not verify_client_secret(SECRET, "not-a-valid-hash")


def test_access_token_contains_scoped_merchant_identity() -> None:
    merchant_id = uuid4()
    token, expires_in = create_access_token("client-test", merchant_id, ["payments:read"])
    claims = decode_access_token(token)

    assert expires_in == 900
    assert claims["sub"] == "client-test"
    assert claims["mid"] == str(merchant_id)
    assert claims["scopes"] == ["payments:read"]
