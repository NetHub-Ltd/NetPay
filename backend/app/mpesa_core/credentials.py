"""Credential encryption, resolution, callback URLs, and API-user credentials."""
import base64
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography import x509
from pydantic import SecretStr

from app.mpesa_core.errors import ConfigurationError, CredentialsUnavailable

if TYPE_CHECKING:
    from app.core.config import Settings
    from app.models.integrations import DarajaIntegration


_KEY_ID = re.compile(r"^[A-Za-z0-9_-]{1,32}$")


@dataclass(frozen=True, repr=False)
class IntegrationCredentials:
    """Plaintext credentials held only in memory for one provider operation."""

    consumer_key: str
    consumer_secret: str
    passkey: str | None
    initiator_name: str | None
    initiator_password: str | None


class CredentialVault:
    """Encrypt fields with a Fernet keyring supplied outside the database.

    Configure MPESA_CREDENTIAL_ENCRYPTION_KEYS as comma-separated key-id=key
    entries and MPESA_CREDENTIAL_ACTIVE_KEY_ID as the key used for new writes.
    Ciphertext stores its key ID so old keys can remain available during rotation.
    """

    def __init__(self, settings: "Settings") -> None:
        self._settings = settings
        raw = settings.mpesa_credential_encryption_keys
        if raw is None or not raw.get_secret_value().strip():
            raise ConfigurationError("MPESA_CREDENTIAL_ENCRYPTION_KEYS is required")
        self._keys: dict[str, bytes] = {}
        for entry in raw.get_secret_value().split(","):
            key_id, separator, key_value = entry.strip().partition("=")
            if not separator or not _KEY_ID.fullmatch(key_id) or not key_value:
                raise ConfigurationError("invalid M-Pesa credential keyring format")
            try:
                Fernet(key_value.encode("ascii"))
            except (ValueError, UnicodeEncodeError) as exc:
                raise ConfigurationError("invalid Fernet key in M-Pesa credential keyring") from exc
            self._keys[key_id] = key_value.encode("ascii")
        if settings.mpesa_credential_active_key_id not in self._keys:
            raise ConfigurationError("active M-Pesa credential key ID is absent from keyring")

    def encrypt(self, value: str) -> bytes:
        """Encrypt one credential and prefix it with the active key identifier."""
        key_id = self._settings.mpesa_credential_active_key_id
        token = Fernet(self._keys[key_id]).encrypt(value.encode("utf-8"))
        return key_id.encode("ascii") + b":" + token

    def decrypt(self, ciphertext: bytes | None) -> str:
        """Decrypt a stored credential using its recorded key ID."""
        if not ciphertext:
            raise CredentialsUnavailable("integration credential is missing")
        key_id_bytes, separator, token = ciphertext.partition(b":")
        if not separator:
            raise CredentialsUnavailable("stored credential has no key identifier")
        try:
            key_id = key_id_bytes.decode("ascii")
            key = self._keys[key_id]
            return Fernet(key).decrypt(token).decode("utf-8")
        except (KeyError, UnicodeDecodeError, InvalidToken, ValueError) as exc:
            raise CredentialsUnavailable("stored credential cannot be decrypted with configured keyring") from exc

    def store(
        self,
        integration: "DarajaIntegration",
        *,
        consumer_key: str,
        consumer_secret: str,
        passkey: str | None = None,
        initiator_name: str | None = None,
        initiator_password: str | None = None,
    ) -> None:
        """Store only encrypted provider secrets on the integration model."""
        integration.consumer_key_ciphertext = self.encrypt(consumer_key)
        integration.consumer_secret_ciphertext = self.encrypt(consumer_secret)
        integration.passkey_ciphertext = self.encrypt(passkey) if passkey else None
        integration.initiator_name = initiator_name
        integration.initiator_password_ciphertext = (
            self.encrypt(initiator_password) if initiator_password else None
        )
        integration.credential_status = "pending"
        integration.credentials_validated_at = None
        integration.status = "pending"
        integration.credential_version += 1

    def rotate(self, integration: "DarajaIntegration") -> None:
        """Re-encrypt existing fields with the active key without exporting plaintext."""
        credentials = self.resolve(integration)
        integration.consumer_key_ciphertext = self.encrypt(credentials.consumer_key)
        integration.consumer_secret_ciphertext = self.encrypt(credentials.consumer_secret)
        integration.passkey_ciphertext = self.encrypt(credentials.passkey) if credentials.passkey else None
        integration.initiator_password_ciphertext = (
            self.encrypt(credentials.initiator_password) if credentials.initiator_password else None
        )
        integration.credential_version += 1

    def resolve(self, integration: "DarajaIntegration") -> IntegrationCredentials:
        """Resolve an integration's secrets only for an internal provider call."""
        return IntegrationCredentials(
            consumer_key=self.decrypt(integration.consumer_key_ciphertext),
            consumer_secret=self.decrypt(integration.consumer_secret_ciphertext),
            passkey=self.decrypt(integration.passkey_ciphertext) if integration.passkey_ciphertext else None,
            initiator_name=integration.initiator_name,
            initiator_password=(
                self.decrypt(integration.initiator_password_ciphertext)
                if integration.initiator_password_ciphertext
                else None
            ),
        )


def generate_security_credential(
    integration: "DarajaIntegration",
    credentials: IntegrationCredentials,
    settings: "Settings",
) -> str:
    """Encrypt the API initiator password using the environment's Safaricom X.509 certificate."""
    if not credentials.initiator_password:
        raise CredentialsUnavailable("API initiator password is not configured")
    certificate_secret: SecretStr | None = (
        settings.mpesa_production_certificate_pem
        if integration.environment == "production"
        else settings.mpesa_sandbox_certificate_pem
    )
    if certificate_secret is None:
        raise ConfigurationError("the environment-specific Daraja public certificate is required")
    try:
        certificate = x509.load_pem_x509_certificate(certificate_secret.get_secret_value().encode("utf-8"))
        public_key = certificate.public_key()
        if not isinstance(public_key, rsa.RSAPublicKey):
            raise ConfigurationError("Daraja certificate must contain an RSA public key")
        encrypted = public_key.encrypt(credentials.initiator_password.encode("utf-8"), padding.PKCS1v15())
        return base64.b64encode(encrypted).decode("ascii")
    except ValueError as exc:
        raise ConfigurationError("the configured Daraja certificate is invalid") from exc


def build_callback_urls(settings: "Settings", integration: "DarajaIntegration") -> tuple[str, str, str]:
    """Build stable NetPay callback URLs; production must always use HTTPS."""
    from urllib.parse import urlsplit

    base = (settings.mpesa_public_base_url or "").rstrip("/")
    parsed = urlsplit(base)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.query or parsed.fragment:
        raise ConfigurationError("MPESA_PUBLIC_BASE_URL must be an absolute origin or base URL")
    if integration.environment == "production" and parsed.scheme != "https":
        raise ConfigurationError("production M-Pesa callback URLs must use HTTPS")
    if parsed.username or parsed.password:
        raise ConfigurationError("MPESA_PUBLIC_BASE_URL must not contain credentials")
    integration_id = integration.integration_id
    return (
        f"{base}/callbacks/mpesa/stk/{integration_id}",
        f"{base}/callbacks/mpesa/c2b/validation/{integration_id}",
        f"{base}/callbacks/mpesa/c2b/confirmation/{integration_id}",
    )
