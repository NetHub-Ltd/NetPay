"""HTTPS-only webhook destination validation with private-network blocking."""

import ipaddress
import socket
from urllib.parse import urlsplit


class UnsafeWebhookURL(ValueError):
    """A webhook URL is not a safe public HTTPS destination."""


def validate_public_https_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise UnsafeWebhookURL("Webhook URL must use HTTPS and include a hostname")
    if parsed.username is not None or parsed.password is not None or parsed.fragment:
        raise UnsafeWebhookURL("Webhook URL must not include credentials or a fragment")

    hostname = parsed.hostname.rstrip(".").lower()
    if hostname in {"localhost", "metadata.google.internal"} or hostname.endswith((".localhost", ".local", ".internal", ".test", ".invalid", ".example")):
        raise UnsafeWebhookURL("Webhook hostname is not publicly routable")
    port = parsed.port or 443

    try:
        literal = ipaddress.ip_address(hostname)
        addresses = [literal]
    except ValueError:
        try:
            resolved = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise UnsafeWebhookURL("Webhook hostname could not be resolved") from exc
        addresses = []
        for item in resolved:
            try:
                addresses.append(ipaddress.ip_address(item[4][0]))
            except ValueError as exc:
                raise UnsafeWebhookURL("Webhook hostname resolved to an invalid address") from exc

    if not addresses or any(not address.is_global for address in addresses):
        raise UnsafeWebhookURL("Webhook hostname must resolve only to public IP addresses")
