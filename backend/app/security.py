"""M2M credential hashing primitives."""

import base64
import hashlib
import hmac
import secrets

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_KEY_LENGTH = 32


def hash_client_secret(secret: str) -> str:
    if len(secret) < 32:
        raise ValueError("Client secrets must contain at least 32 characters")
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        secret.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_KEY_LENGTH,
    )
    encode = lambda value: base64.urlsafe_b64encode(value).decode("ascii")
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${encode(salt)}${encode(digest)}"


def verify_client_secret(secret: str, encoded: str) -> bool:
    try:
        algorithm, n_raw, r_raw, p_raw, salt_raw, digest_raw = encoded.split("$", 5)
        if algorithm != "scrypt":
            return False
        n, r, p = int(n_raw), int(r_raw), int(p_raw)
        if n != _SCRYPT_N or r != _SCRYPT_R or p != _SCRYPT_P:
            return False
        decode = lambda value: base64.urlsafe_b64decode(value.encode("ascii"))
        salt = decode(salt_raw)
        expected = decode(digest_raw)
        actual = hashlib.scrypt(
            secret.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=len(expected)
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, UnicodeEncodeError):
        return False
