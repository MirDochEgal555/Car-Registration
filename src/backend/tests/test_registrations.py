from __future__ import annotations

from dataclasses import replace
from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.services.email import OutgoingEmail, get_email_sender


class RecordingEmailSender:
    def __init__(self) -> None:
        self.messages: list[OutgoingEmail] = []

    def send(self, email: OutgoingEmail) -> None:
        self.messages.append(email)


def _valid_tire_storage_draft(**overrides: object) -> dict[str, object]:
    draft: dict[str, object] = {
        "id": str(uuid4()),
        "service_type": "tire_storage",
        "service_date": str(date.today()),
        "mechanic_id": str(uuid4()),
        "vehicle": {"license_plate": "cw ab 123", "mileage_km": 73400},
        "tire_sets": [
            {
                "role": "stored",
                "tire_set": {
                    "tire_type": "winter",
                    "quantity": 4,
                    "width_mm": 205,
                    "aspect_ratio": 55,
                    "rim_diameter_inch": 16,
                },
            }
        ],
    }
    draft.update(overrides)
    return draft


def test_validate_returns_draft_and_review_hints() -> None:
    draft = _valid_tire_storage_draft(
        field_status={"tire_sets.0.tire_set.model": "uncertain"}
    )

    response = TestClient(app).post("/api/v1/registrations/validate", json=draft)

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is True
    assert payload["review_required"] is True
    assert payload["registration"]["vehicle"]["license_plate"] == "CW-AB 123"
    assert payload["field_status"] == {"tire_sets.0.tire_set.model": "uncertain"}
    assert payload["status"] == "mechanic_review"


def test_validate_reports_missing_handoff_fields_without_claiming_review() -> None:
    response = TestClient(app).post("/api/v1/registrations/validate", json={})

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is False
    assert payload["review_required"] is False
    assert {issue["field"] for issue in payload["issues"]} == {
        "service_type",
        "service_date",
        "mechanic_id",
        "vehicle.license_plate",
    }


def test_validate_marks_implausible_tread_depth_without_correcting_it() -> None:
    draft = _valid_tire_storage_draft(
        tire_sets=[
            {
                "role": "stored",
                "tire_set": {
                    "tires": [{"position": "front_left", "tread_depth_mm": 65}],
                },
            }
        ]
    )

    response = TestClient(app).post("/api/v1/registrations/validate", json=draft)

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is False
    assert payload["review_required"] is True
    assert payload["registration"]["tire_sets"][0]["tire_set"]["tires"][0]["tread_depth_mm"] == "65"
    assert payload["field_status"]["tire_sets.0.tire_set.tires.0.tread_depth_mm"] == "invalid"


def test_send_requires_explicit_mechanic_confirmation() -> None:
    response = TestClient(app).post(
        "/api/v1/registrations/send", json=_valid_tire_storage_draft()
    )

    assert response.status_code == 422


def test_send_rejects_a_draft_with_required_values_missing() -> None:
    response = TestClient(app).post(
        "/api/v1/registrations/send", json={"mechanic_confirmed": True}
    )

    assert response.status_code == 409
    assert response.json()["detail"]["validation"]["valid"] is False


def test_send_delivers_rendered_email(monkeypatch: object) -> None:
    from app.api.v1.routes import registrations

    sender = RecordingEmailSender()
    monkeypatch.setattr(
        registrations,
        "settings",
        replace(registrations.settings, office_email="office@example.com"),
    )
    app.dependency_overrides[get_email_sender] = lambda: sender
    try:
        response = TestClient(app).post(
            "/api/v1/registrations/send",
            json=_valid_tire_storage_draft(mechanic_confirmed=True),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "email_sent"
    assert response.json()["recipient"] == "office@example.com"
    assert len(sender.messages) == 1
    assert "Kennzeichen: CW-AB 123" in sender.messages[0].body
    assert "tire_sets.0.tire_set" not in sender.messages[0].body
