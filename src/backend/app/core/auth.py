"""Password and signed-session helpers for the workshop login."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time


def verify_password(password: str, encoded_hash: str) -> bool:
    """Verify a PBKDF2-SHA256 password hash without storing plain passwords."""

    try:
        algorithm, iterations_text, salt, expected = encoded_hash.split("$", 3)
        iterations = int(iterations_text)
        if algorithm != "pbkdf2_sha256" or iterations < 100_000 or not salt:
            return False
        derived = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), iterations
        )
        actual = base64.b64encode(derived).decode()
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(actual, expected)


def create_password_hash(password: str, iterations: int = 600_000) -> str:
    """Create the environment-variable format documented for operators."""

    salt = secrets.token_urlsafe(18)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${base64.b64encode(digest).decode()}"


def create_session(username: str, secret: str, ttl_seconds: int) -> str:
    payload = {
        "username": username,
        "expires_at": int(time.time()) + ttl_seconds,
        "nonce": secrets.token_urlsafe(18),
    }
    encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def read_session(value: str | None, secret: str) -> str | None:
    """Return the logged-in username only for an intact, unexpired session."""

    if not value or "." not in value:
        return None
    encoded, signature = value.rsplit(".", 1)
    expected = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        padded = encoded + "=" * (-len(encoded) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        username = payload["username"]
        expires_at = payload["expires_at"]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(username, str) or not isinstance(expires_at, int) or expires_at < time.time():
        return None
    return username
