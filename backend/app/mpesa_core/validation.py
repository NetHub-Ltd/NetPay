"""Input normalization and protocol-boundary validation."""
from __future__ import annotations

import re
from urllib.parse import urlparse

from app.mpesa_core.errors import CapabilityDisabled, InvalidRequest
from app.mpesa_core.schemas import IntegrationContext


_PHONE_RE = re.compile(r"^(?:254|\+254|0)?((?:7\d{8}|1[01]\d{7}))$")


def normalize_ke_phone(value: str) -> str:
    """Normalize common Kenyan MSISDN forms to 254XXXXXXXXX."""
    candidate = value.strip().replace(" ", "").replace("-", "")
    match = _PHONE_RE.fullmatch(candidate)
    if not match:
        raise InvalidRequest("phone_number must be a valid Kenyan mobile number")
    return f"254{match.group(1)}"


def validate_callback_url(url: str, *, production: bool) -> str:
    """Validate an absolute HTTP(S) callback URL and require HTTPS in production."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise InvalidRequest("callback URL must be an absolute HTTP(S) URL")
    if production and parsed.scheme != "https":
        raise InvalidRequest("production callback URLs must use HTTPS")
    if parsed.username or parsed.password:
        raise InvalidRequest("callback URLs must not embed credentials")
    return url


def require_capability(context: IntegrationContext, capability: str) -> None:
    """Fail before network I/O when the integration has not enabled a capability."""
    if capability not in context.enabled_capabilities:
        raise CapabilityDisabled(f"capability '{capability}' is not enabled for this integration")


def validate_context(context: IntegrationContext) -> None:
    """Validate minimum integration prerequisites without exposing credential values."""
    if not context.credentials.consumer_key.get_secret_value():
        raise InvalidRequest("consumer key is missing")
    if not context.credentials.consumer_secret.get_secret_value():
        raise InvalidRequest("consumer secret is missing")
    if context.environment == "production" and not context.shortcode:
        raise InvalidRequest("production shortcode is required")
