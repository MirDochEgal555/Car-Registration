"""Application settings loaded from the process environment."""

from __future__ import annotations

from dataclasses import dataclass
import os


def _environment_flag(name: str, default: bool = False) -> bool:
    """Read a conventional boolean environment variable."""

    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Settings needed by the HTTP API and SMTP delivery adapter."""

    app_name: str = "CarTech API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    office_email: str | None = os.getenv("CARTECH_OFFICE_EMAIL")
    smtp_host: str | None = os.getenv("CARTECH_SMTP_HOST")
    smtp_port: int = int(os.getenv("CARTECH_SMTP_PORT", "587"))
    smtp_username: str | None = os.getenv("CARTECH_SMTP_USERNAME")
    smtp_password: str | None = os.getenv("CARTECH_SMTP_PASSWORD")
    smtp_from: str | None = os.getenv("CARTECH_SMTP_FROM")
    smtp_use_tls: bool = _environment_flag("CARTECH_SMTP_USE_TLS", default=True)
    smtp_use_ssl: bool = _environment_flag("CARTECH_SMTP_USE_SSL")


settings = Settings()
