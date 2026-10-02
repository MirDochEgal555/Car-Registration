"""Tests for the lean transcript-only office email."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.registration import RegistrationDraft
from app.services.registration_email import render_registration_email
from app.services.registration_validation import validate_registration


def test_registration_email_contains_only_the_verbatim_transcript() -> None:
    transcript = "  Bitte <prüfen> & Rückmeldung geben.\nZweite Zeile.  "
    draft = RegistrationDraft.model_validate(
        {
            "service_type": "tire_storage",
            "service_date": "2026-08-20",
            "mechanic_id": "c2feb07e-4854-4ef8-9e8a-14d8468df624",
            "vehicle": {"license_plate": "cw ab 123", "mileage_km": 73400},
            "tire_sets": [
                {"role": "stored", "tire_set": {"tire_type": "winter", "quantity": 4}}
            ],
            "raw_transcript": transcript,
        }
    )

    email = render_registration_email(
        validate_registration(draft),
        "office@example.com",
        datetime(2026, 8, 20, 10, 42, tzinfo=timezone.utc),
    )

    assert email.subject == "CarTech · CW-AB 123 · 20.08.2026"
    assert email.html_body is not None
    assert transcript in email.body
    assert "Bitte &lt;prüfen&gt; &amp; Rückmeldung geben.\nZweite Zeile." in email.html_body
    for value in (
        "Reifeneinlagerung",
        "Reifenwechsel",
        "Winterreifen",
        "Vorgang",
        "Fahrzeugdaten",
        "Reifendaten",
        "Prüfhinweise",
        "Transkript\n",
    ):
        assert value not in email.subject
        assert value not in email.body
        assert value not in email.html_body
    assert "Kennzeichen: CW-AB 123" in email.body
    assert "Kennzeichen: <strong>CW-AB 123</strong>" in email.html_body


def test_registration_email_keeps_an_empty_transcript_empty() -> None:
    draft = RegistrationDraft.model_validate({"raw_transcript": ""})

    email = render_registration_email(
        validate_registration(draft),
        "office@example.com",
        datetime(2026, 8, 20, 10, 42, tzinfo=timezone.utc),
    )

    assert email.body == ""
