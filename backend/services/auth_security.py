import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from backend.config.auth import (
    AUTH_SECRET,
    AUTH_TOKEN_EXPIRE_SECONDS,
    PASSWORD_HASH_ITERATIONS,
)


class TokenValidationError(ValueError):
    pass


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_HASH_ITERATIONS,
    )
    return (
        f"pbkdf2_sha256${PASSWORD_HASH_ITERATIONS}"
        f"${salt}${derived.hex()}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt, expected_hash = password_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations_text),
    )
    return hmac.compare_digest(derived.hex(), expected_hash)


def create_access_token(user_id: int) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + AUTH_TOKEN_EXPIRE_SECONDS,
    }
    signing_input = ".".join(
        [
            _encode_segment(header),
            _encode_segment(payload),
        ]
    )
    signature = hmac.new(
        AUTH_SECRET.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_base64url_encode(signature)}"


def decode_access_token(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise TokenValidationError("invalid token format")

    signing_input = ".".join(parts[:2])
    provided_signature = _base64url_decode(parts[2])
    expected_signature = hmac.new(
        AUTH_SECRET.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(provided_signature, expected_signature):
        raise TokenValidationError("invalid token signature")

    payload = _decode_segment(parts[1])
    expires_at = payload.get("exp")
    if not isinstance(expires_at, int) or expires_at < int(time.time()):
        raise TokenValidationError("token expired")
    return payload


def _encode_segment(value: dict[str, Any]) -> str:
    return _base64url_encode(
        json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )


def _decode_segment(value: str) -> dict[str, Any]:
    try:
        decoded = _base64url_decode(value).decode("utf-8")
        return json.loads(decoded)
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise TokenValidationError("invalid token payload") from exc


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))
    except ValueError as exc:
        raise TokenValidationError("invalid token encoding") from exc
