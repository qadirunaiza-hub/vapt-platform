import pytest
from app.utils.validators import (
    validate_ip_address, validate_hostname, validate_url,
    validate_target_address, safe_hostname_for_nmap,
)


def test_valid_ips():
    assert validate_ip_address("192.168.1.1") is True
    assert validate_ip_address("10.0.0.1") is True
    assert validate_ip_address("2001:db8::1") is True


def test_blocked_metadata_ip():
    assert validate_ip_address("169.254.169.254") is False


def test_valid_hostname():
    assert validate_hostname("example.com") is True
    assert validate_hostname("sub.domain.internal") is True


def test_invalid_hostname():
    assert validate_hostname("-bad.com") is False
    assert validate_hostname("a" * 254) is False


def test_valid_url():
    assert validate_url("https://example.com") is not None
    assert validate_url("http://192.168.1.10:8080") is not None


def test_blocked_metadata_url():
    assert validate_url("http://169.254.169.254/latest/meta-data") is None


def test_unsafe_url_scheme():
    assert validate_url("ftp://example.com") is None


def test_safe_hostname_for_nmap_valid():
    assert safe_hostname_for_nmap("192.168.1.1") == "192.168.1.1"
    assert safe_hostname_for_nmap("example.com") == "example.com"


def test_safe_hostname_for_nmap_invalid():
    with pytest.raises(ValueError):
        safe_hostname_for_nmap("169.254.169.254")

    with pytest.raises(ValueError):
        safe_hostname_for_nmap("$(whoami)")

    with pytest.raises(ValueError):
        safe_hostname_for_nmap("example.com; rm -rf /")


def test_target_address_web():
    assert validate_target_address("https://app.internal", "web_application") is True
    assert validate_target_address("not-a-url", "web_application") is False


def test_target_address_docker():
    assert validate_target_address("nginx:latest", "docker_image") is True
    assert validate_target_address("my-registry.io/myapp:1.0", "docker_image") is True
    assert validate_target_address("$(evil)", "docker_image") is False
