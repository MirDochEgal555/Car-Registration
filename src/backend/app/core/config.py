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
    """Read a positive SMTP timeout in seconds from the environment."""

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


def _environment_origins(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    """Read an explicit comma-separated allow-list for browser origins."""

    value = _environment_value(name)
    if value is None:
        return default
    return tuple(origin.strip() for origin in value.split(",") if origin.strip())


@dataclass(frozen=True)
class Settings:
    """Settings needed by the HTTP API and SMTP delivery adapter."""

    app_name: str = "CarTech API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
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
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: _environment_origins(
            "CARTECH_CORS_ORIGINS",
            ("http://localhost:5173", "http://127.0.0.1:5173"),
        )
    )


settings = Settings()
