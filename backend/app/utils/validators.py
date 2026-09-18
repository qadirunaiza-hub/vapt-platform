"""
Input validation for scan targets.
All target addresses must pass these checks before being passed to scanners.
"""
import re
import ipaddress
from typing import Optional
from urllib.parse import urlparse


_HOSTNAME_RE = re.compile(
    r"^(?!-)[A-Z\d\-]{1,63}(?<!-)$",
    re.IGNORECASE,
)

_PRIVATE_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]

# SSRF protection: block cloud metadata endpoints
_BLOCKED_HOSTS = {
    "169.254.169.254",  # AWS/GCP/Azure metadata
    "metadata.google.internal",
    "metadata.internal",
}


def validate_ip_address(address: str) -> bool:
    try:
        ipaddress.ip_address(address)
        return address not in _BLOCKED_HOSTS
    except ValueError:
        return False


def validate_hostname(hostname: str) -> bool:
    if hostname in _BLOCKED_HOSTS:
        return False
    if len(hostname) > 253:
        return False
    parts = hostname.rstrip(".").split(".")
    return all(_HOSTNAME_RE.match(part) for part in parts)


def validate_url(url: str) -> Optional[str]:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return None
        host = parsed.hostname or ""
        if host in _BLOCKED_HOSTS:
            return None
        if not (validate_hostname(host) or validate_ip_address(host)):
            return None
        return url
    except Exception:
        return None


def validate_target_address(address: str, target_type: str) -> bool:
    """
    Validate a target address based on its type.
    Returns True only if the address is safe to pass to scanners.
    """
    if target_type in ("web_application", "api"):
        return validate_url(address) is not None
    if target_type == "host_ip":
        return validate_ip_address(address) or validate_hostname(address)
    if target_type == "docker_image":
        # Docker image names: alphanumeric, slashes, colons, hyphens, dots
        return bool(re.match(r"^[a-z0-9][a-z0-9._\-/:]*(:[a-z0-9._\-]+)?$", address, re.IGNORECASE))
    if target_type == "source_repository":
        # Local paths only for Phase 1
        return bool(re.match(r"^(/[^/\0]+)+$", address))
    return False


def safe_hostname_for_nmap(address: str) -> Optional[str]:
    """
    Return the address only if it is safe to pass as an Nmap argument.
    Raises ValueError otherwise to prevent injection.
    """
    if validate_ip_address(address):
        return address
    if validate_hostname(address):
        return address
    raise ValueError(f"Address failed validation for scanner use: {address!r}")
