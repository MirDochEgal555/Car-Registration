"""Tests for the Phase 7 LLM Structured-Output extraction contract."""

from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.models.extraction import StructuredExtractionResult, structured_extraction_json_schema


def _field(value: object, field_status: str) -> dict[str, object]:
    return {"value": value, "field_status": field_status}


def _missing_fields(*names: str) -> dict[str, dict[str, object]]:
    return {name: _field(None, "missing") for name in names}


def _minimal_result() -> dict[str, object]:
    return {
        "service_type": _field("tire_storage", "valid"),
        "service_date": _field(None, "missing"),
        "vehicle": _missing_fields(
            "license_plate",
            "mileage_km",
            "make",
            "model",
            "propulsion_type",
            "first_registration_month",
            "max_speed_kmh",
            "vin",
        ),
        "notes": _field(None, "missing"),
        "tire_sets": _field(None, "missing"),
        "tire_inspections": _field(None, "missing"),
        "conditions": _field(None, "missing"),
        "visual_inspections": _field(None, "missing"),
        "tire_change_details": _field(None, "missing"),
        "review_required": False,
    }


def _walk_objects(value: object):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from _walk_objects(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_objects(item)


def test_schema_is_closed_and_requires_all_known_properties() -> None:
    schema = structured_extraction_json_schema()

    for object_schema in _walk_objects(schema):
        if object_schema.get("type") == "object":
            assert object_schema["additionalProperties"] is False
            assert set(object_schema["required"]) == set(object_schema["properties"])


def test_schema_supports_unknown_values_as_null_without_review() -> None:
    result = StructuredExtractionResult.model_validate(_minimal_result())

    assert result.vehicle.model.value is None
    assert result.vehicle.model.field_status.value == "missing"
    assert result.review_required is False


@pytest.mark.parametrize("field_status", ["missing", "uncertain"])
def test_missing_or_uncertain_values_cannot_be_populated(field_status: str) -> None:
    payload = _minimal_result()
    payload["vehicle"]["model"] = _field("invented model", field_status)  # type: ignore[index]
    payload["review_required"] = field_status == "uncertain"

    with pytest.raises(ValidationError, match="must have value null"):
        StructuredExtractionResult.model_validate(payload)


def test_invalid_value_is_preserved_and_sets_record_review() -> None:
    payload = _minimal_result()
    payload["tire_sets"] = _field(
        [
            {
                "role": _field("stored", "valid"),
                "tire_set": {
                    **_missing_fields(
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
                    ),
                },
            }
        ],
        "valid",
    )
    tire_set = payload["tire_sets"]["value"][0]["tire_set"]  # type: ignore[index]
    tire_set["quantity"] = _field(0, "invalid")
    payload["review_required"] = True

    result = StructuredExtractionResult.model_validate(payload)

    assert result.tire_sets.value is not None
    assert result.tire_sets.value[0].tire_set.quantity.value == 0
    assert result.review_required is True


def test_review_required_must_match_nested_field_statuses() -> None:
    payload = _minimal_result()
    payload["vehicle"]["model"] = _field(None, "uncertain")  # type: ignore[index]

    with pytest.raises(ValidationError, match="review_required"):
        StructuredExtractionResult.model_validate(payload)

    reviewed_payload = deepcopy(payload)
    reviewed_payload["review_required"] = True
    assert StructuredExtractionResult.model_validate(reviewed_payload).review_required
