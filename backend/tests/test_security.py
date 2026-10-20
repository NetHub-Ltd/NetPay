from app.security import hash_client_secret, verify_client_secret


SECRET = "test-client-secret-that-is-at-least-32-characters-long"


def test_client_secret_hash_verifies_only_matching_secret() -> None:
    encoded = hash_client_secret(SECRET)

    assert encoded.startswith("scrypt$")
    assert SECRET not in encoded
    assert verify_client_secret(SECRET, encoded)
    assert not verify_client_secret("different-client-secret-value-long-enough", encoded)


def test_malformed_secret_hash_fails_closed() -> None:
    assert not verify_client_secret(SECRET, "not-a-valid-hash")
