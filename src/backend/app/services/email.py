"""SMTP delivery adapter for the MVP's structured office email."""

from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol

from app.core.config import Settings, settings


class EmailConfigurationError(RuntimeError):
    """Raised when email delivery is requested without a usable configuration."""


class EmailDeliveryError(RuntimeError):
    """Raised when a configured mail server cannot accept a message."""


@dataclass(frozen=True)
class OutgoingEmail:
    """The rendered email handed to a delivery adapter."""

    recipient: str
    subject: str
    body: str


class EmailSender(Protocol):
    """Small seam that lets delivery be tested without an SMTP server."""

    def send(self, email: OutgoingEmail) -> None:
        """Deliver an email or raise an application-specific error."""


class SmtpEmailSender:
    """Send plain-text messages through the SMTP settings in ``Settings``."""

    def __init__(self, configuration: Settings) -> None:
        self._configuration = configuration

    def send(self, email: OutgoingEmail) -> None:
        configuration = self._configuration
        if not configuration.smtp_host or not configuration.smtp_from:
            raise EmailConfigurationError(
                "SMTP is not configured. Set CARTECH_SMTP_HOST and CARTECH_SMTP_FROM."
            )

        message = EmailMessage()
        message["From"] = configuration.smtp_from
        message["To"] = email.recipient
        message["Subject"] = email.subject
        message.set_content(email.body)

        try:
            if configuration.smtp_use_ssl:
                smtp_client: smtplib.SMTP = smtplib.SMTP_SSL(
                    configuration.smtp_host,
                    configuration.smtp_port,
                    timeout=15,
                )
            else:
                smtp_client = smtplib.SMTP(
                    configuration.smtp_host,
                    configuration.smtp_port,
                    timeout=15,
                )

            with smtp_client:
                if configuration.smtp_use_tls and not configuration.smtp_use_ssl:
                    smtp_client.starttls()
                if configuration.smtp_username:
                    smtp_client.login(
                        configuration.smtp_username,
                        configuration.smtp_password or "",
                    )
                smtp_client.send_message(message)
        except (OSError, smtplib.SMTPException) as error:
            raise EmailDeliveryError("The office email could not be delivered.") from error


def get_email_sender() -> EmailSender:
    """FastAPI dependency returning the configured production mail adapter."""

    return SmtpEmailSender(settings)
