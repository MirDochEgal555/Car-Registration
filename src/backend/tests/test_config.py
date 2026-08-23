"""Tests for deployment configuration read from environment variables."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.services.email import EmailConfigurationError, OutgoingEmail, SmtpEmailSender


def test_settings_reads_smtp_values_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CARTECH_OFFICE_EMAIL", "office@example.com")
    monkeypatch.setenv("CARTECH_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("CARTECH_SMTP_PORT", "465")
    monkeypatch.setenv("CARTECH_SMTP_USERNAME", "mailer")
    monkeypatch.setenv("CARTECH_SMTP_PASSWORD", "not-a-real-secret")
    monkeypatch.setenv("CARTECH_SMTP_FROM", "cartech@example.com")
    monkeypatch.setenv("CARTECH_SMTP_USE_TLS", "false")
    monkeypatch.setenv("CARTECH_SMTP_USE_SSL", "true")
    monkeypatch.setenv("CARTECH_SMTP_TIMEOUT_SECONDS", "9.5")

    configuration = Settings()

    assert configuration.office_email == "office@example.com"
    assert configuration.smtp_host == "smtp.example.com"
    assert configuration.smtp_port == 465
    assert configuration.smtp_username == "mailer"
    assert configuration.smtp_password == "not-a-real-secret"
    assert configuration.smtp_from == "cartech@example.com"
    assert configuration.smtp_use_tls is False
    assert configuration.smtp_use_ssl is True
    assert configuration.smtp_timeout_seconds == 9.5


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("CARTECH_SMTP_PORT", "0"),
        ("CARTECH_SMTP_PORT", "not-a-port"),
        ("CARTECH_SMTP_USE_TLS", "perhaps"),
        ("CARTECH_SMTP_TIMEOUT_SECONDS", "0"),
        ("CARTECH_SMTP_TIMEOUT_SECONDS", "nan"),
    ],
)
def test_settings_rejects_invalid_smtp_environment(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValueError, match=name):
        Settings()


@pytest.mark.parametrize(
    "configuration",
    [
        Settings(smtp_from="cartech@example.com"),
        Settings(smtp_host="smtp.example.com"),
        Settings(
            smtp_host="smtp.example.com",
            smtp_from="cartech@example.com",
            smtp_username="mailer",
        ),
        Settings(
            smtp_host="smtp.example.com",
            smtp_from="cartech@example.com",
            smtp_password="not-a-real-secret",
        ),
    ],
)
def test_sender_refuses_incomplete_smtp_configuration(configuration: Settings) -> None:
    with pytest.raises(EmailConfigurationError):
        SmtpEmailSender(configuration).send(
            OutgoingEmail(
                recipient="office@example.com",
                subject="Protokoll",
                body="Textalternative",
            )
        )
