"""Application settings loaded from the process environment."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import os


def _environment_value(name: str) -> str | None:
    """Return a non-empty, trimmed environment value."""

    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _environment_flag(name: str, default: bool = False) -> bool:
    """Read a strictly parsed conventional boolean environment variable."""

    value = _environment_value(name)
    if value is None:
        return default
    normalized = value.lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(
        f"{name} must be one of true, false, 1, 0, yes, no, on, or off."
    )


def _environment_port(name: str, default: int) -> int:
    """Read a valid TCP port from the environment."""

    value = _environment_value(name)
    if value is None:
        return default
    try:
        port = int(value)
    except ValueError as error:
        raise ValueError(f"{name} must be a whole number between 1 and 65535.") from error
    if not 1 <= port <= 65535:
        raise ValueError(f"{name} must be a whole number between 1 and 65535.")
    return port


def _environment_timeout(name: str, default: float) -> float:
    """Read a positive external-service timeout in seconds from the environment."""

    value = _environment_value(name)
    if value is None:
        return default
    try:
        timeout = float(value)
    except ValueError as error:
        raise ValueError(f"{name} must be a positive number of seconds.") from error
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError(f"{name} must be a positive number of seconds.")
    return timeout


def _environment_positive_integer(name: str, default: int) -> int:
    """Read a positive integer setting from the environment."""

    value = _environment_value(name)
    if value is None:
        return default
    try:
        result = int(value)
    except ValueError as error:
        raise ValueError(f"{name} must be a positive whole number.") from error
    if result <= 0:
        raise ValueError(f"{name} must be a positive whole number.")
    return result


def _environment_origins(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    """Read an explicit comma-separated allow-list for browser origins."""

    value = _environment_value(name)
    if value is None:
        return default
    return tuple(origin.strip() for origin in value.split(",") if origin.strip())


@dataclass(frozen=True)
class Settings:
    """Settings needed by the HTTP API and its external service adapters."""

    app_name: str = "CarTech API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    app_auth_enabled: bool = field(
        default_factory=lambda: _environment_flag("CARTECH_APP_AUTH_ENABLED")
    )
    app_auth_username: str | None = field(
        default_factory=lambda: _environment_value("CARTECH_APP_AUTH_USERNAME")
    )
    app_auth_password_hash: str | None = field(
        default_factory=lambda: _environment_value("CARTECH_APP_AUTH_PASSWORD_HASH")
    )
    app_auth_session_secret: str | None = field(
        default_factory=lambda: _environment_value("CARTECH_APP_AUTH_SESSION_SECRET")
    )
    app_auth_session_ttl_seconds: int = field(
        default_factory=lambda: _environment_positive_integer(
            "CARTECH_APP_AUTH_SESSION_TTL_SECONDS", default=28800
        )
    )
    office_email: str | None = field(
        default_factory=lambda: _environment_value("CARTECH_OFFICE_EMAIL")
    )
    smtp_host: str | None = field(
        default_factory=lambda: _environment_value("CARTECH_SMTP_HOST")
    )
    smtp_port: int = field(
        default_factory=lambda: _environment_port("CARTECH_SMTP_PORT", default=587)
    )
    smtp_username: str | None = field(
        default_factory=lambda: _environment_value("CARTECH_SMTP_USERNAME")
    )
    smtp_password: str | None = field(
        default_factory=lambda: _environment_value("CARTECH_SMTP_PASSWORD")
    )
    smtp_from: str | None = field(
        default_factory=lambda: _environment_value("CARTECH_SMTP_FROM")
    )
    smtp_use_tls: bool = field(
        default_factory=lambda: _environment_flag("CARTECH_SMTP_USE_TLS", default=True)
    )
    smtp_use_ssl: bool = field(
        default_factory=lambda: _environment_flag("CARTECH_SMTP_USE_SSL")
    )
    smtp_timeout_seconds: float = field(
        default_factory=lambda: _environment_timeout(
            "CARTECH_SMTP_TIMEOUT_SECONDS", default=15.0
        )
    )
    delivery_store_path: str = field(
        default_factory=lambda: _environment_value("CARTECH_DELIVERY_STORE_PATH")
        or "data/processed/cartech-deliveries.sqlite3"
    )
    openai_api_key: str | None = field(
        default_factory=lambda: _environment_value("CARTECH_OPENAI_API_KEY")
        or _environment_value("OPENAI_API_KEY")
    )
    openai_transcription_model: str = field(
        default_factory=lambda: _environment_value(
            "CARTECH_OPENAI_TRANSCRIPTION_MODEL"
        )
        or "gpt-transcribe"
    )
    openai_extraction_model: str = field(
        default_factory=lambda: _environment_value("CARTECH_OPENAI_EXTRACTION_MODEL")
        or "gpt-4o-mini"
    )
    openai_timeout_seconds: float = field(
        default_factory=lambda: _environment_timeout(
            "CARTECH_OPENAI_TIMEOUT_SECONDS", default=30.0
        )
    )
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: _environment_origins(
            "CARTECH_CORS_ORIGINS",
            ("http://localhost:5173", "http://127.0.0.1:5173"),
        )
    )

    def __post_init__(self) -> None:
        """Refuse to start a supposedly protected deployment half-configured."""

        if not self.app_auth_enabled:
            return
        missing = [
            name
            for name, value in (
                ("CARTECH_APP_AUTH_USERNAME", self.app_auth_username),
                ("CARTECH_APP_AUTH_PASSWORD_HASH", self.app_auth_password_hash),
                ("CARTECH_APP_AUTH_SESSION_SECRET", self.app_auth_session_secret),
            )
            if not value
        ]
        if missing:
            raise ValueError(
                "CARTECH_APP_AUTH_ENABLED requires " + ", ".join(missing) + "."
            )
        if len(self.app_auth_session_secret or "") < 32:
            raise ValueError("CARTECH_APP_AUTH_SESSION_SECRET must contain at least 32 characters.")


settings = Settings()
