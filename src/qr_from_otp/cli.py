"""Generate local terminal QR codes for OTP provisioning."""

import base64
import binascii
from io import StringIO
from urllib.parse import parse_qs, quote, unquote, urlencode, urlsplit, urlunsplit

import pyotp
import qrcode
from cyclopts import App
from qrcode.constants import ERROR_CORRECT_M
from rich.console import Console

console = Console()
error_console = Console(stderr=True)

app = App(
    help="Display a local terminal QR code for a TOTP secret or otpauth URL.",
    console=console,
)


def _is_otpauth_uri(value: str) -> bool:
    """Return whether a value starts with an otpauth URI scheme."""
    return value.strip().lower().startswith("otpauth://")


def _normalise_secret(value: str) -> str:
    """Normalize and validate a Base32 OTP secret."""
    secret = value.replace(" ", "").replace("-", "").upper()
    secret = secret.rstrip("=")
    if not secret:
        raise ValueError("OTP secret must not be empty")
    if "=" in secret:
        raise ValueError("OTP secret must be a valid Base32 value")
    try:
        base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("OTP secret must be a valid Base32 value") from exc
    return secret


def _validate_otpauth_uri(value: str) -> None:
    """Validate an otpauth URI and its embedded secret."""
    parts = urlsplit(value)
    query = parse_qs(parts.query)
    secret = query.get("secret", [""])[0]
    if (
        parts.scheme.lower() != "otpauth"
        or parts.netloc.lower() not in {"totp", "hotp"}
        or not parts.path
        or not secret
    ):
        raise ValueError("malformed otpauth:// URL")
    _normalise_secret(secret)


def _extract_name_and_issuer(value: str) -> tuple[str, str]:
    """Extract the account name and issuer from an otpauth URI."""
    _validate_otpauth_uri(value)
    parts = urlsplit(value)
    query = parse_qs(parts.query)
    label = unquote(parts.path.lstrip("/"))
    name = label
    label_issuer = ""
    if ":" in label:
        label_issuer, name = label.split(":", maxsplit=1)

    issuer = query.get("issuer", [""])[0] or label_issuer
    if not name:
        raise ValueError("malformed otpauth:// URL")
    return name, issuer


def _update_otpauth_uri(
    value: str,
    *,
    name: str | None = None,
    issuer: str | None = None,
) -> str:
    """Return an otpauth URI with an updated account name and issuer."""
    if name is None and issuer is None:
        return value

    parts = urlsplit(value)
    query = parse_qs(parts.query)
    if name is None or issuer is None:
        current_name, current_issuer = _extract_name_and_issuer(value)
        name = current_name if name is None else name
        issuer = current_issuer if issuer is None else issuer
    if issuer is not None:
        query["issuer"] = [issuer]
    label = f"{issuer}:{name}" if issuer else name
    return urlunsplit(
        parts._replace(
            path=f"/{quote(label, safe=':')}",
            query=urlencode(query, doseq=True),
        )
    )


def _provisioning_uri(
    value: str,
    *,
    name: str | None = None,
    issuer: str | None = None,
) -> str:
    """Return an otpauth URI for a secret or full URI."""
    value = value.strip()
    if _is_otpauth_uri(value):
        _validate_otpauth_uri(value)
        return _update_otpauth_uri(value, name=name, issuer=issuer)

    secret = _normalise_secret(value)
    name, issuer = _resolve_name_and_issuer(name=name, issuer=issuer)
    return pyotp.TOTP(secret).provisioning_uri(name=name, issuer_name=issuer)


def _resolve_name_and_issuer(
    *,
    name: str | None,
    issuer: str | None,
) -> tuple[str, str]:
    """Return labels with defaults for a secret-based provisioning URI."""
    return (
        "OTP account" if name is None else name,
        "Local OTP" if issuer is None else issuer,
    )


def _scan_label(
    *,
    secret: str,
    name: str | None = None,
    issuer: str | None = None,
) -> str:
    """Return the instruction shown above the terminal QR code."""
    if _is_otpauth_uri(secret):
        extracted_name, extracted_issuer = _extract_name_and_issuer(secret)
        name = extracted_name if name is None else name
        issuer = extracted_issuer if issuer is None else issuer
    else:
        name, issuer = _resolve_name_and_issuer(name=name, issuer=issuer)

    return f"Scan this QR code with your authenticator app ({issuer} / {name}):"


@app.default
def _run(
    secret: str,
    name: str | None = None,
    issuer: str | None = None,
) -> None:
    """Display a terminal QR code for an OTP secret or provisioning URI.

    Parameters
    ----------
    secret:
        Base32 TOTP secret or complete otpauth:// URL.
    name:
        Account label used when generating a URI from a secret.
    issuer:
        Issuer label used when generating a URI from a secret.
    """

    secret = secret.strip()
    try:
        uri = _provisioning_uri(secret, name=name, issuer=issuer)
    except ValueError as exc:
        error_console.print("Error:", str(exc), style="bold red")
        raise SystemExit(2) from None

    qr = qrcode.QRCode(
        error_correction=ERROR_CORRECT_M,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)

    output = StringIO()
    qr.print_ascii(out=output)
    console.print(_scan_label(secret=secret, name=name, issuer=issuer), style="bold white")
    console.print(output.getvalue(), markup=False, end="")

def main() -> None:
    app()


if __name__ == "__main__":
    main()
