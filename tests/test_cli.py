from urllib.parse import parse_qs, urlsplit

import pytest

from qr_from_otp.cli import (
    _extract_name_and_issuer,
    _normalise_secret,
    _provisioning_uri,
    _update_otpauth_uri,
)

SECRET = "JBSWY3DPEHPK3PXP"
URI = (
    "otpauth://totp/Example:alice%40example.com"
    f"?secret={SECRET}&issuer=Example&algorithm=SHA1&digits=6&period=30"
)


def test_extract_name_and_issuer_from_uri() -> None:
    assert _extract_name_and_issuer(URI) == ("alice@example.com", "Example")


def test_extract_name_uses_label_issuer_when_query_issuer_is_missing() -> None:
    uri = f"otpauth://totp/Example:alice%40example.com?secret={SECRET}"

    assert _extract_name_and_issuer(uri) == ("alice@example.com", "Example")


def test_update_uri_preserves_settings_and_updates_labels() -> None:
    updated = _update_otpauth_uri(
        URI,
        name="bob@example.com",
        issuer="New Example",
    )
    parts = urlsplit(updated)

    assert parts.path == "/New%20Example:bob%40example.com"
    query = parse_qs(parts.query)
    assert query["secret"] == [SECRET]
    assert query["issuer"] == ["New Example"]
    assert query["algorithm"] == ["SHA1"]
    assert query["digits"] == ["6"]
    assert query["period"] == ["30"]


@pytest.mark.parametrize("value", ["", "not-base32", "1234567"])
def test_uri_operations_reject_invalid_secret(value: str) -> None:
    uri = f"otpauth://totp/Example:alice?secret={value}"

    with pytest.raises(ValueError):
        _provisioning_uri(uri)


def test_normalise_secret_accepts_spaces_hyphens_and_padding() -> None:
    assert _normalise_secret("JBSW Y3D-PEHP K3PXP===") == SECRET