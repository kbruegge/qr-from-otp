# qr-from-otp

A small, fully local terminal tool that turns a Base32 TOTP secret or a complete `otpauth://` URL into a QR code for scanning into an authenticator app.

I needed this because I had some OTP codes in my locally hosted Vaultwarden instance that I wanted to scan into my phone without sending the secret to a third-party QR generator. This tool is written in Python and uses only local libraries.


## Install

Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/):

```sh
uv sync
```

To install the command as a standalone tool from this checkout, run:

```sh
uv tool install .
```

After installation, use it from any directory:

```sh
qr-from-otp JBSWY3DPEHPK3PXP
```


The runtime dependencies are downloaded only during installation. Generating the QR code does not make network requests.

## Usage

```sh
uv run qr-from-otp JBSWY3DPEHPK3PXP
uv run qr-from-otp JBSWY3DPEHPK3PXP --issuer "Example" --name alice@example.com
uv run qr-from-otp 'otpauth://totp/Example:alice%40example.com?secret=JBSWY3DPEHPK3PXP&issuer=Example'
```

The name and issuer are optional. If not provided, the name is extracted from the `otpauth://` URL if present. But the CLI parameters take precedence over the URL. 

__Note:__ Keep in mind that the secret is passed as a command-line argument. This can expose it in shell history or process listings; clear shell history afterward or use a shell mechanism that avoids recording the argument.

Invalid or empty Base32 secrets and malformed `otpauth://` URLs are rejected without generating output. Embedded URL secrets are validated as Base32 values. Spaces and hyphens in a Base32 secret are accepted and removed.

## Library choice

The following libraries are used:

- [Cyclopts](https://cyclopts.readthedocs.io/en/stable/) provides typed command-line parsing and Rich-formatted help and errors.
- PyOTP builds standards-compatible `otpauth://` provisioning URIs and implements RFC 6238 TOTP.
- [qrcode](https://pypi.org/project/qrcode/) is a pure-Python QR generator with built-in ASCII terminal output via `print_ascii`.

## Development note

Parts of this codebase were created with AI assistance; not all of it was.
