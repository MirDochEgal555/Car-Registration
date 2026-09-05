"""Tests for the matching office-email alternatives."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.config import Settings
from app.models.registration import RegistrationDraft
from app.services.email import OutgoingEmail, SmtpEmailSender
from app.services.registration_email import render_registration_email
from app.services.registration_validation import validate_registration


def _validation_with_note(note: str):
    draft = RegistrationDraft.model_validate(
        {
            "service_type": "tire_storage",
            "service_date": "2026-08-20",
            "mechanic_id": "c2feb07e-4854-4ef8-9e8a-14d8468df624",
            "vehicle": {"license_plate": "cw ab 123"},
            "notes": note,
            "tire_sets": [
                {
                    "role": "stored",
                    "tire_set": {"tire_type": "winter", "quantity": 4},
                }
            ],
            "field_status": {"notes": "uncertain"},
        }
    )
    return validate_registration(draft)


def test_registration_email_renders_text_and_html_from_the_same_document() -> None:
    email = render_registration_email(
        _validation_with_note("Bitte <prüfen> & Rückmeldung geben"),
        "office@example.com",
        datetime(2026, 8, 20, 10, 42, tzinfo=timezone.utc),
    )

    assert email.html_body is not None
    for value in (
        "Reifeneinlagerung",
        "CW-AB 123",
        "Winterreifen",
        "Vorgang",
        "Fahrzeugdaten",
        "Reifendaten",
        "Notizen & Service",
        "Unsicher",
    ):
        assert value in email.body
        assert value.replace("&", "&amp;") in email.html_body
    assert "Bitte <prüfen> & Rückmeldung geben" in email.body
    assert "Bitte &lt;prüfen&gt; &amp; Rückmeldung geben" in email.html_body
    assert "Bitte <prüfen> & Rückmeldung geben" not in email.html_body


def test_registration_email_groups_complete_tire_change_data() -> None:
    draft = RegistrationDraft.model_validate(
        {
            "service_type": "tire_change",
            "service_date": "2026-08-20",
            "mechanic_id": "c2feb07e-4854-4ef8-9e8a-14d8468df624",
            "vehicle": {
                "license_plate": "cw ab 123",
                "mileage_km": 73400,
            },
            "notes": "Kundin wegen Termin anrufen",
            "tire_sets": [
                {
                    "role": "installed",
                    "tire_set": {
                        "tire_type": "winter",
                        "width_mm": 205,
                        "aspect_ratio": 55,
                        "rim_diameter_inch": 16,
                        "manufacturer": "Continental",
                        "model": "WinterContact TS 870",
                        "quantity": 4,
                    },
                }
            ],
            "tire_inspections": [
                {
                    "tire_set_role": "installed",
                    "tread_front_left_mm": "6.5",
                    "tread_front_right_mm": "6.0",
                    "tread_rear_left_mm": "5.5",
                    "tread_rear_right_mm": "5.0",
                }
            ],
            "conditions": [
                {
                    "tire_set_role": "installed",
                    "condition": "cracked",
                    "position": "rear_right",
                }
            ],
            "tire_change_details": {"wheel_change_performed": True},
        }
    )
    email = render_registration_email(
        validate_registration(draft),
        "office@example.com",
        datetime(2026, 8, 20, 10, 42, tzinfo=timezone.utc),
    )

    assert email.html_body is not None
    for value in (
        "Vorgangstyp",
        "Reifenwechsel",
        "Zeitstempel",
        "Fahrzeugdaten",
        "Kennzeichen",
        "CW-AB 123",
        "Kilometerstand",
        "73400 km",
        "Reifendaten",
        "Winterreifen",
        "Reifengröße",
        "205/55 R16",
        "Hersteller / Modell",
        "Continental / WinterContact TS 870",
        "Anzahl",
        "Profiltiefe vorne links",
        "Profiltiefe vorne rechts",
        "Profiltiefe hinten links",
        "Profiltiefe hinten rechts",
        "Rissig",
        "Notizen & Service",
        "Kundin wegen Termin anrufen",
        "Räder gewechselt",
    ):
        assert value in email.body
        assert value.replace("&", "&amp;") in email.html_body


class _RecordingSmtp:
    def __init__(self, *_: object, **__: object) -> None:
        self.message = None
        self.started_tls = False

    def __enter__(self) -> "_RecordingSmtp":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def starttls(self, **_: object) -> None:
        self.started_tls = True

    def login(self, _: str, __: str) -> None:
        return None

    def send_message(self, message: object) -> None:
        self.message = message


def test_smtp_sender_uses_multipart_alternative_for_html_email(monkeypatch: object) -> None:
    from app.services import email as email_service

    smtp_client = _RecordingSmtp()
    monkeypatch.setattr(email_service.smtplib, "SMTP", lambda *_args, **_kwargs: smtp_client)
    sender = SmtpEmailSender(
        Settings(smtp_host="smtp.example.com", smtp_from="cartech@example.com")
    )

    sender.send(
        OutgoingEmail(
            recipient="office@example.com",
            subject="Protokoll",
            body="Textalternative",
            html_body="<p>HTML-Alternative</p>",
        )
    )

    assert smtp_client.started_tls is True
    assert smtp_client.message is not None
    assert smtp_client.message.get_content_type() == "multipart/alternative"
    alternatives = list(smtp_client.message.iter_parts())
    assert [part.get_content_type() for part in alternatives] == ["text/plain", "text/html"]
    assert alternatives[0].get_content().strip() == "Textalternative"
    assert alternatives[1].get_content().strip() == "<p>HTML-Alternative</p>"


def test_smtp_sender_uses_implicit_tls_when_configured(monkeypatch: object) -> None:
    from app.services import email as email_service

    smtp_client = _RecordingSmtp()
    monkeypatch.setattr(
        email_service.smtplib, "SMTP_SSL", lambda *_args, **_kwargs: smtp_client
    )
    sender = SmtpEmailSender(
        Settings(
            smtp_host="smtp.example.com",
            smtp_from="cartech@example.com",
            smtp_use_ssl=True,
        )
    )

    sender.send(
        OutgoingEmail(
            recipient="office@example.com",
            subject="Protokoll",
            body="Textalternative",
        )
    )

    assert smtp_client.started_tls is False
