"""API integration tests for the complete Phase-7 extraction pipeline.

The external model is replaced by a deterministic provider that returns the
same strict Structured-Output shape an OpenAI request would return.  Therefore
every documented workshop case executes the production path:

``transcript -> provider -> normalisation -> extraction validation ->
RegistrationDraft -> registration validation``.
"""

from __future__ import annotations

from copy import deepcopy
import asyncio
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.v1.routes.extraction import get_extraction_provider
from app.main import app
from app.services.extraction_provider import (
    ExtractionProviderError,
    ExtractionProviderUnavailableError,
    OpenAIStructuredExtractionProvider,
)
from app.services.registration_validation import normalize_license_plate


_FIXTURE_PATH = Path(__file__).parents[3] / "data/fixtures/workshop_e2e_cases.json"
_TIRE_SET_FIELDS = (
    "tire_type",
    "width_mm",
    "aspect_ratio",
    "rim_diameter_inch",
    "rim_category",
    "rim_manufacturer",
    "rim_model",
    "manufacturer",
    "model",
    "quantity",
    "dot",
    "load_index",
    "speed_index",
    "notes",
    "tires",
)
_TIRE_FIELDS = (
    "position",
    "manufacturer",
    "profile",
    "tread_depth_mm",
    "dot",
    "wear_marks_present",
    "has_damage",
    "damage_notes",
)
_INSPECTION_FIELDS = (
    "tire_set_role",
    "tread_front_left_mm",
    "tread_front_right_mm",
    "tread_rear_left_mm",
    "tread_rear_right_mm",
    "tread_front_mm",
    "tread_rear_mm",
    "notes",
)
_CONDITION_FIELDS = ("tire_set_role", "condition", "position", "notes")
_VISUAL_INSPECTION_FIELDS = (
    "tire_set_role",
    "component",
    "result",
    "position",
    "notes",
)
_TIRE_CHANGE_DETAIL_FIELDS = (
    "wheel_change_performed",
    "balancing_steel_count",
    "balancing_alloy_count",
    "machine_wash_count",
    "manual_wash_count",
    "whm_mode",
    "next_customer_service",
    "next_oil_service",
    "air_pressure_front_bar",
    "air_pressure_rear_bar",
    "wheel_lock_present",
    "wheel_bolt_configuration",
    "hu_due_month",
    "suspension_visual_result",
    "brake_visual_result",
    "hub_cleaned",
    "rdks_type",
    "rdks_programmed",
    "speed_limiter_set",
    "speed_limiter_sticker_applied",
    "wheel_bolt_torque_nm",
    "whatsapp_contact_allowed",
    "brake_disc_measurements",
)


class FixtureExtractionProvider:
    """Return one recorded Structured-Output object and retain its input."""

    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.transcripts: list[str] = []

    async def extract(self, transcript: str) -> dict[str, object]:
        self.transcripts.append(transcript)
        return deepcopy(self.payload)


class UnavailableExtractionProvider:
    async def extract(self, transcript: str) -> dict[str, object]:
        del transcript
        raise ExtractionProviderUnavailableError("Extraktion ist nicht eingerichtet.")


class FakeOpenAICompletions:
    def __init__(self, content: str) -> None:
        self.content = content
        self.requests: list[dict[str, object]] = []

    async def create(self, **request: object) -> object:
        self.requests.append(request)
        message = type("Message", (), {"content": self.content})()
        choice = type("Choice", (), {"message": message})()
        return type("Completion", (), {"choices": [choice]})()


class FakeExtractionClient:
    def __init__(self, content: str) -> None:
        completions = FakeOpenAICompletions(content)
        self.chat = type("Chat", (), {"completions": completions})()


def _load_cases() -> list[dict[str, object]]:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


PHASE_7_CASES = _load_cases()


def _field(value: object = None, field_status: str = "missing") -> dict[str, object]:
    return {"value": value, "field_status": field_status}


def _wrapped_object(names: tuple[str, ...]) -> dict[str, dict[str, object]]:
    return {name: _field() for name in names}


def _empty_tire() -> dict[str, object]:
    return _wrapped_object(_TIRE_FIELDS)


def _empty_tire_set() -> dict[str, object]:
    tire_set = _wrapped_object(_TIRE_SET_FIELDS)
    tire_set["tires"] = _field()
    return tire_set


def _empty_tire_change_details() -> dict[str, object]:
    details = _wrapped_object(_TIRE_CHANGE_DETAIL_FIELDS)
    details["brake_disc_measurements"] = _field()
    return details


def _empty_result() -> dict[str, object]:
    return {
        "service_type": _field(),
        "service_date": _field(),
        "vehicle": _wrapped_object(
            (
                "license_plate",
                "mileage_km",
                "make",
                "model",
                "propulsion_type",
                "first_registration_month",
                "max_speed_kmh",
                "vin",
            )
        ),
        "notes": _field(),
        "tire_sets": _field(),
        "tire_inspections": _field(),
        "conditions": _field(),
        "visual_inspections": _field(),
        "tire_change_details": _field(),
        "review_required": False,
    }


def _structured_output_for(case: dict[str, object]) -> dict[str, object]:
    """Encode the fixture draft as the provider's complete strict JSON shape."""

    result = _empty_result()
    source = case.get("provider_draft", case["draft"])
    assert isinstance(source, dict)
    _apply_draft_values(result, source)
    # ``field_status`` is the provider's status decision, not a value source.
    source_statuses = case["draft"].get("field_status", {})  # type: ignore[index]
    assert isinstance(source_statuses, dict)
    for path, field_status in source_statuses.items():
        _set_status(result, str(path), str(field_status))
    result["review_required"] = _review_required(result)
    return result


def _apply_draft_values(result: dict[str, object], draft: dict[str, object]) -> None:
    for name in ("service_type", "service_date", "notes"):
        if name in draft:
            result[name] = _field(draft[name], "valid")

    vehicle = draft.get("vehicle")
    if isinstance(vehicle, dict):
        for name, value in vehicle.items():
            result["vehicle"][name] = _field(value, "valid")  # type: ignore[index]

    if "tire_sets" in draft:
        tire_sets: list[dict[str, object]] = []
        for relation in draft["tire_sets"]:  # type: ignore[index]
            tire_set = _empty_tire_set()
            relation_value = relation["tire_set"]
            for name, value in relation_value.items():
                if name == "tires":
                    tire_set[name] = _field(
                        [_tire_with_values(item) for item in value], "valid"
                    )
                else:
                    tire_set[name] = _field(value, "valid")
            tire_sets.append(
                {"role": _field(relation["role"], "valid"), "tire_set": tire_set}
            )
        result["tire_sets"] = _field(tire_sets, "valid")

    result["tire_inspections"] = _list_field(
        draft.get("tire_inspections"), _INSPECTION_FIELDS
    )
    result["conditions"] = _list_field(draft.get("conditions"), _CONDITION_FIELDS)
    result["visual_inspections"] = _list_field(
        draft.get("visual_inspections"), _VISUAL_INSPECTION_FIELDS
    )

    if "tire_change_details" in draft:
        details = _empty_tire_change_details()
        for name, value in draft["tire_change_details"].items():  # type: ignore[index]
            if name == "brake_disc_measurements":
                details[name] = _field(
                    [
                        {
                            "position": _field(item.get("position"), "valid"),
                            "thickness_mm": _field(item.get("thickness_mm"), "valid"),
                        }
                        for item in value
                    ],
                    "valid",
                )
            else:
                details[name] = _field(value, "valid")
        result["tire_change_details"] = _field(details, "valid")


def _tire_with_values(values: dict[str, object]) -> dict[str, object]:
    tire = _empty_tire()
    for name, value in values.items():
        tire[name] = _field(value, "valid")
    return tire


def _list_field(
    items: object, names: tuple[str, ...]
) -> dict[str, object]:
    if not isinstance(items, list):
        return _field()
    result: list[dict[str, object]] = []
    for item in items:
        assert isinstance(item, dict)
        entry = _wrapped_object(names)
        for name, value in item.items():
            entry[name] = _field(value, "valid")
        result.append(entry)
    return _field(result, "valid")


def _set_status(payload: dict[str, object], path: str, field_status: str) -> None:
    wrapper = _wrapper_at_path(payload, path)
    wrapper["field_status"] = field_status
    if field_status in {"missing", "uncertain"}:
        wrapper["value"] = None


def _wrapper_at_path(payload: dict[str, object], path: str) -> dict[str, object]:
    current: object = payload
    for segment in path.split("."):
        if isinstance(current, dict) and set(current) == {"value", "field_status"}:
            current = current["value"]
        if isinstance(current, dict):
            current = current[segment]
        elif isinstance(current, list):
            current = current[int(segment)]
        else:  # pragma: no cover - fixture errors are surfaced as a clear assertion
            raise AssertionError(f"No wrapper at {path}")
    assert isinstance(current, dict)
    assert set(current) == {"value", "field_status"}
    return current


def _review_required(value: object) -> bool:
    if isinstance(value, dict):
        if value.get("field_status") in {"uncertain", "invalid"}:
            return True
        return any(_review_required(item) for item in value.values())
    if isinstance(value, list):
        return any(_review_required(item) for item in value)
    return False


def _assert_subset(expected: object, actual: object, path: str = "") -> None:
    if isinstance(expected, dict):
        assert isinstance(actual, dict)
        for key, value in expected.items():
            if key == "field_status":
                continue
            assert key in actual
            _assert_subset(value, actual[key], f"{path}.{key}" if path else key)
    elif isinstance(expected, list):
        assert isinstance(actual, list)
        assert len(actual) >= len(expected)
        for expected_item, actual_item in zip(expected, actual):
            _assert_subset(expected_item, actual_item, path)
    elif path == "vehicle.license_plate" and isinstance(expected, str):
        assert actual == normalize_license_plate(expected)
    elif path.endswith(".tire_type") and expected == "unknown" and actual is None:
        # The deterministic validation turns an explicit unknown into an
        # unresolved value; its `uncertain` status is asserted separately.
        return
    elif isinstance(expected, (int, float)) and isinstance(actual, str):
        try:
            assert Decimal(actual) == Decimal(str(expected))
        except InvalidOperation:
            pytest.fail(f"Expected numeric value at {path}, got {actual!r}.")
    else:
        assert actual == expected


@pytest.mark.parametrize("case", PHASE_7_CASES, ids=lambda case: str(case["id"]))
def test_documented_phase_7_case_runs_through_the_public_extraction_api(
    case: dict[str, object],
) -> None:
    """Make every documented Phase-7 case executable without a live API key."""

    provider = FixtureExtractionProvider(_structured_output_for(case))
    app.dependency_overrides[get_extraction_provider] = lambda: provider
    try:
        response = TestClient(app).post(
            "/api/v1/extractions", json={"transcript": case["input"]}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    assert provider.transcripts == [case["input"]]
    body = response.json()
    assert body["registration"]["raw_transcript"] == case["input"]
    _assert_subset(case["draft"], body["registration"])

    expected_statuses = {
        **case.get("expected_field_status", {}),
        **case.get("expected_pipeline_field_status", {}),
    }
    for field, expected_status in expected_statuses.items():
        assert body["field_status"][field] == expected_status
        assert body["registration"]["field_status"][field] == expected_status
    assert body["review_required"] is case.get(
        "expected_pipeline_review_required",
        case.get("expected_review_required", False),
    )


def test_blank_transcript_is_rejected_without_calling_the_provider() -> None:
    provider = FixtureExtractionProvider(_empty_result())
    app.dependency_overrides[get_extraction_provider] = lambda: provider
    try:
        response = TestClient(app).post("/api/v1/extractions", json={"transcript": " \n "})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert provider.transcripts == []


def test_extraction_api_reports_an_unconfigured_provider_without_a_partial_draft() -> None:
    app.dependency_overrides[get_extraction_provider] = UnavailableExtractionProvider
    try:
        response = TestClient(app).post(
            "/api/v1/extractions", json={"transcript": "Vier Winterreifen."}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["detail"] == "Extraktion ist nicht eingerichtet."


def test_openai_provider_uses_the_central_strict_schema_and_verbatim_transcript() -> None:
    payload = _structured_output_for(PHASE_7_CASES[0])
    client = FakeExtractionClient(json.dumps(payload))
    provider = OpenAIStructuredExtractionProvider(
        api_key="not-a-real-secret", client=client
    )
    transcript = "  CW AB 123, vier Winterreifen.  \n"

    assert asyncio.run(provider.extract(transcript)) == payload
    request = client.chat.completions.requests[0]
    assert request["response_format"]["json_schema"]["strict"] is True
    assert transcript in request["messages"][0]["content"]


def test_openai_provider_rejects_non_object_responses() -> None:
    client = FakeExtractionClient("[]")
    provider = OpenAIStructuredExtractionProvider(
        api_key="not-a-real-secret", client=client
    )

    with pytest.raises(ExtractionProviderError, match="kein strukturiertes Objekt"):
        asyncio.run(provider.extract("Vier Winterreifen."))
