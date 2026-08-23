from __future__ import annotations

from dataclasses import replace
from datetime import date
from pathlib import Path
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.models.enums import ServiceStatus
from app.models.registration import RegistrationDraft
from app.services.delivery_store import DeliveryStore
from app.services.email import EmailDeliveryError, OutgoingEmail, get_email_sender


class RecordingEmailSender:
    def __init__(self) -> None:
        self.messages: list[OutgoingEmail] = []

    def send(self, email: OutgoingEmail) -> None:
        self.messages.append(email)


class FailingEmailSender:
    def send(self, email: OutgoingEmail) -> None:
        raise EmailDeliveryError("The office email could not be delivered.")


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


def _delivery_store(path: Path) -> DeliveryStore:
    return DeliveryStore(path / "deliveries.sqlite3")


def test_send_delivers_rendered_email(monkeypatch: object, tmp_path: Path) -> None:
    from app.api.v1.routes import registrations

    sender = RecordingEmailSender()
    delivery_store = _delivery_store(tmp_path)
    monkeypatch.setattr(
        registrations,
        "settings",
        replace(registrations.settings, office_email="office@example.com"),
    )
    app.dependency_overrides[get_email_sender] = lambda: sender
    app.dependency_overrides[registrations.get_delivery_store] = lambda: delivery_store
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
    assert sender.messages[0].html_body is not None
    assert "Kennzeichen: <strong>CW-AB 123</strong>" in sender.messages[0].html_body


def test_failed_delivery_is_saved_and_retryable(
    monkeypatch: object, tmp_path: Path
) -> None:
    from app.api.v1.routes import registrations

    delivery_store = _delivery_store(tmp_path)
    draft = _valid_tire_storage_draft(
        mechanic_confirmed=True,
        raw_transcript="CW AB 123, vier Winterreifen.",
    )
    registration_id = draft["id"]
    monkeypatch.setattr(
        registrations,
        "settings",
        replace(registrations.settings, office_email="office@example.com"),
    )
    app.dependency_overrides[get_email_sender] = FailingEmailSender
    app.dependency_overrides[registrations.get_delivery_store] = lambda: delivery_store
    try:
        failed_response = TestClient(app).post(
            "/api/v1/registrations/send", json=draft
        )

        successful_sender = RecordingEmailSender()
        app.dependency_overrides[get_email_sender] = lambda: successful_sender
        status_response = TestClient(app).get(
            f"/api/v1/registrations/{registration_id}/delivery-status"
        )
        retry_response = TestClient(app).post(
            f"/api/v1/registrations/{registration_id}/retry"
        )
    finally:
        app.dependency_overrides.clear()

    assert failed_response.status_code == 502
    failure = failed_response.json()["detail"]
    assert failure["delivery"]["registration_id"] == registration_id
    assert failure["delivery"]["status"] == "email_failed"
    assert failure["delivery"]["attempt_count"] == 1
    assert failure["retry_endpoint"].endswith(f"/{registration_id}/retry")

    assert status_response.status_code == 200
    assert status_response.json()["status"] == "email_failed"
    assert status_response.json()["last_error"] == "The office email could not be delivered."

    persisted = delivery_store.get(UUID(registration_id))
    assert persisted is not None
    assert persisted.registration.vehicle.license_plate == "CW-AB 123"
    assert persisted.registration.raw_transcript is None

    assert retry_response.status_code == 200
    assert retry_response.json()["status"] == "email_sent"
    assert retry_response.json()["attempt_count"] == 2
    assert len(successful_sender.messages) == 1


def test_successful_send_is_idempotent_for_the_registration_id(
    monkeypatch: object, tmp_path: Path
) -> None:
    from app.api.v1.routes import registrations

    sender = RecordingEmailSender()
    delivery_store = _delivery_store(tmp_path)
    draft = _valid_tire_storage_draft(mechanic_confirmed=True)
    monkeypatch.setattr(
        registrations,
        "settings",
        replace(registrations.settings, office_email="office@example.com"),
    )
    app.dependency_overrides[get_email_sender] = lambda: sender
    app.dependency_overrides[registrations.get_delivery_store] = lambda: delivery_store
    try:
        first_response = TestClient(app).post("/api/v1/registrations/send", json=draft)
        second_response = TestClient(app).post("/api/v1/registrations/send", json=draft)
        retry_response = TestClient(app).post(
            f"/api/v1/registrations/{draft['id']}/retry"
        )
    finally:
        app.dependency_overrides.clear()

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["attempt_count"] == 1
    assert retry_response.status_code == 409
    assert len(sender.messages) == 1


def test_missing_office_address_keeps_the_registration_for_later_retry(
    monkeypatch: object, tmp_path: Path
) -> None:
    from app.api.v1.routes import registrations

    delivery_store = _delivery_store(tmp_path)
    draft = _valid_tire_storage_draft(mechanic_confirmed=True)
    registration_id = draft["id"]
    monkeypatch.setattr(
        registrations,
        "settings",
        replace(registrations.settings, office_email=None),
    )
    app.dependency_overrides[get_email_sender] = RecordingEmailSender
    app.dependency_overrides[registrations.get_delivery_store] = lambda: delivery_store
    try:
        failed_response = TestClient(app).post(
            "/api/v1/registrations/send", json=draft
        )
        monkeypatch.setattr(
            registrations,
            "settings",
            replace(registrations.settings, office_email="office@example.com"),
        )
        successful_sender = RecordingEmailSender()
        app.dependency_overrides[get_email_sender] = lambda: successful_sender
        retry_response = TestClient(app).post(
            f"/api/v1/registrations/{registration_id}/retry"
        )
    finally:
        app.dependency_overrides.clear()

    assert failed_response.status_code == 503
    assert failed_response.json()["detail"]["delivery"]["status"] == "email_failed"
    assert retry_response.status_code == 200
    assert retry_response.json()["recipient"] == "office@example.com"


def test_interrupted_delivery_attempt_is_made_retryable_on_recovery(
    tmp_path: Path,
) -> None:
    delivery_store = _delivery_store(tmp_path)
    draft = RegistrationDraft.model_validate(
        _valid_tire_storage_draft(mechanic_confirmed=True)
    )
    delivery_store.save_or_get(draft, "office@example.com")
    claimed = delivery_store.start_attempt(draft.id, "office@example.com")

    assert claimed.status is ServiceStatus.EMAIL_SENDING
    assert delivery_store.recover_interrupted_attempts() == 1

    recovered = delivery_store.get(draft.id)
    assert recovered is not None
    assert recovered.status is ServiceStatus.EMAIL_FAILED
    assert recovered.attempt_count == 1
    assert recovered.last_error is not None
    assert "erneut versendet" in recovered.last_error
