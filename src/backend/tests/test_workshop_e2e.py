"""End-to-end regression tests for the documented anonymised workshop cases.

The extraction adapter (speech-to-text/LLM) is intentionally not part of the
backend yet.  These tests exercise its contract boundary: each realistic
transcript is paired with the structured result defined in
``documentation/TEST_CASES.md`` and runs through validation, confirmation,
durable outbox storage, and rendered office email.
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import replace
from datetime import date
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest
from fastapi.testclient import TestClient

from app.api.v1.routes import registrations
from app.main import app
from app.models.registration import RegistrationDraft
from app.services.delivery_store import DeliveryStore
from app.services.email import OutgoingEmail, get_email_sender
from app.services.registration_validation import normalize_license_plate


_FIXTURE_PATH = Path(__file__).parents[3] / "data/fixtures/workshop_e2e_cases.json"
_MECHANIC_ID = "3c0a5fe3-b1b7-4f9f-a9e0-4fc653c2a96e"
_WORKFLOW_VEHICLE = {"license_plate": "CW AT 999"}


class RecordingEmailSender:
    """In-process office mailbox used to verify the fully rendered message."""

    def __init__(self) -> None:
        self.messages: list[OutgoingEmail] = []

    def send(self, email: OutgoingEmail) -> None:
        self.messages.append(email)


def _load_cases() -> list[dict[str, object]]:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


WORKSHOP_CASES = _load_cases()
CASES_BY_ID = {str(case["id"]): case for case in WORKSHOP_CASES}


def _payload_for(case: dict[str, object]) -> dict[str, object]:
    """Combine UI-owned handoff data with the documented extraction result."""

    extraction = deepcopy(case["draft"])
    assert isinstance(extraction, dict)
    extracted_vehicle = extraction.pop("vehicle", {})
    assert isinstance(extracted_vehicle, dict)
    return {
        "id": str(uuid5(NAMESPACE_URL, f"cartech-e2e/{case['id']}")),
        # Protocol type, date and mechanic are supplied by the UI, not guessed
        # from the spoken input.  The fallback plate represents a plate entered
        # before an otherwise vehicle-independent utterance.
        "service_date": str(date.today()),
        "mechanic_id": _MECHANIC_ID,
        "vehicle": {**_WORKFLOW_VEHICLE, **extracted_vehicle},
        "raw_transcript": case["input"],
        **extraction,
    }


def _expected_registration(payload: dict[str, object]) -> dict[str, object]:
    """Produce the public draft form after the one permitted normalization."""

    expected = RegistrationDraft.model_validate(payload).model_dump(mode="json")
    plate = expected["vehicle"]["license_plate"]
    if plate:
        expected["vehicle"]["license_plate"] = normalize_license_plate(plate)
    return expected


@pytest.mark.parametrize("case", WORKSHOP_CASES, ids=lambda case: str(case["id"]))
def test_documented_workshop_case_survives_validation_unchanged(
    case: dict[str, object],
) -> None:
    """Run every documented realistic utterance through the public API."""

    payload = _payload_for(case)
    response = TestClient(app).post("/api/v1/registrations/validate", json=payload)

    assert response.status_code == 200
    body = response.json()
    expected = _expected_registration(payload)
    expected_status = dict(expected["field_status"])
    expected_status.update(case.get("expected_field_status", {}))

    # The response must preserve every extracted value: especially the final
    # correction in a transcript, absent values as null, and distinct tire sets.
    assert body["registration"] == expected
    assert body["field_status"] == expected_status
    assert body["valid"] is case.get("expected_valid", True)
    assert body["review_required"] is case.get("expected_review_required", False)
    assert body["status"] == "mechanic_review"


@pytest.mark.parametrize(
    "case_id, expected_mail_values",
    [
        ("20-einlagerung-einzelreifen", ("Reifeneinlagerung", "Dezent", "Riss in der Seitenwand")),
        ("23-vollstaendiges-reifenwechselprotokoll", ("Reifenwechsel", "WinterContact TS 870", "Kratzer", "120 Nm")),
    ],
)
def test_realistic_workshop_record_reaches_office_via_outbox(
    case_id: str,
    expected_mail_values: tuple[str, ...],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Verify the complete mechanic-review-to-office handoff for both protocols."""

    case = CASES_BY_ID[case_id]
    payload = _payload_for(case)
    validation_response = TestClient(app).post(
        "/api/v1/registrations/validate", json=payload
    )
    assert validation_response.status_code == 200
    assert validation_response.json()["valid"] is True

    sender = RecordingEmailSender()
    store = DeliveryStore(tmp_path / "deliveries.sqlite3")
    monkeypatch.setattr(
        registrations,
        "settings",
        replace(registrations.settings, office_email="office@example.com"),
    )
    app.dependency_overrides[get_email_sender] = lambda: sender
    app.dependency_overrides[registrations.get_delivery_store] = lambda: store
    try:
        send_response = TestClient(app).post(
            "/api/v1/registrations/send",
            json={**payload, "mechanic_confirmed": True},
        )
        status_response = TestClient(app).get(
            f"/api/v1/registrations/{payload['id']}/delivery-status"
        )
    finally:
        app.dependency_overrides.clear()

    assert send_response.status_code == 200
    assert send_response.json()["status"] == "email_sent"
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "email_sent"
    assert status_response.json()["attempt_count"] == 1

    assert len(sender.messages) == 1
    email = sender.messages[0]
    assert all(value in email.body for value in expected_mail_values)
    assert email.html_body is not None
    assert all(value in email.html_body for value in expected_mail_values)
    assert str(case["input"]) not in email.body

    persisted = store.get(UUID(str(payload["id"])))
    assert persisted is not None
    assert persisted.registration.raw_transcript is None
    assert persisted.registration.model_dump(mode="json") == {
        **_expected_registration({**payload, "mechanic_confirmed": True}),
        "raw_transcript": None,
    }
