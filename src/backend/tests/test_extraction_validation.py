"""Unit tests for the deterministic post-normalization validation layer."""

from __future__ import annotations

from copy import deepcopy

from app.models.extraction import StructuredExtractionResult
from app.services.extraction import normalize_and_validate_extraction_response
from app.services.extraction_validation import validate_extraction_payload


def _field(value: object, field_status: str = "valid") -> dict[str, object]:
    return {"value": value, "field_status": field_status}


def _missing(*names: str) -> dict[str, dict[str, object]]:
    return {name: _field(None, "missing") for name in names}


def _tire(position: str, tread_depth_mm: float) -> dict[str, object]:
    return {
        "position": _field(position),
        "manufacturer": _field("Continental"),
        "profile": _field("PremiumContact 7"),
        "tread_depth_mm": _field(tread_depth_mm),
        **_missing("dot", "wear_marks_present", "has_damage", "damage_notes"),
    }


def _payload() -> dict[str, object]:
    """Return a complete, normalised and plausibly valid extraction payload."""

    return {
        "service_type": _field("tire_storage"),
        "service_date": _field(None, "missing"),
        "vehicle": {
            "license_plate": _field("CW-AB 123"),
            "mileage_km": _field(63500),
            "make": _field("Ford"),
            "model": _field("Focus"),
            **_missing(
                "propulsion_type",
                "first_registration_month",
                "max_speed_kmh",
                "vin",
            ),
        },
        "notes": _field(None, "missing"),
        "tire_sets": _field(
            [
                {
                    "role": _field("stored"),
                    "tire_set": {
                        "tire_type": _field("winter"),
                        "width_mm": _field(205),
                        "aspect_ratio": _field(55),
                        "rim_diameter_inch": _field(16),
                        **_missing(
                            "rim_category",
                            "rim_manufacturer",
                            "rim_model",
                        ),
                        "manufacturer": _field("Continental"),
                        "model": _field("WinterContact TS 870"),
                        "quantity": _field(4),
                        **_missing(
                            "dot",
                            "load_index",
                            "speed_index",
                            "notes",
                        ),
                        "tires": _field(
                            [
                                _tire("front_left", 6.5),
                                _tire("front_right", 6.4),
                                _tire("rear_left", 6.0),
                                _tire("rear_right", 6.1),
                            ]
                        ),
                    },
                }
            ]
        ),
        "tire_inspections": _field(
            [
                {
                    "tire_set_role": _field("stored"),
                    **_missing(
                        "tread_front_left_mm",
                        "tread_front_right_mm",
                        "tread_rear_left_mm",
                        "tread_rear_right_mm",
                    ),
                    "tread_front_mm": _field(6.5),
                    "tread_rear_mm": _field(6.0),
                    "notes": _field(None, "missing"),
                }
            ]
        ),
        "conditions": _field(
            [
                {
                    "tire_set_role": _field("stored"),
                    "condition": _field("worn"),
                    "position": _field("rear_right"),
                    "notes": _field(None, "missing"),
                }
            ]
        ),
        "visual_inspections": _field(
            [
                {
                    "tire_set_role": _field("stored"),
                    "component": _field("tire"),
                    "result": _field("ok"),
                    "position": _field("all"),
                    "notes": _field(None, "missing"),
                }
            ]
        ),
        "tire_change_details": _field(None, "missing"),
        "review_required": False,
    }


def _tire_set(payload: dict[str, object]) -> dict[str, object]:
    return payload["tire_sets"]["value"][0]["tire_set"]  # type: ignore[index]


def test_validation_accepts_plausible_normalized_extraction_data() -> None:
    validated = validate_extraction_payload(_payload())
    result = StructuredExtractionResult.model_validate(validated)

    assert result.review_required is False
    assert result.vehicle.mileage_km.field_status.value == "valid"
    assert result.tire_sets.value is not None
    assert result.tire_sets.value[0].tire_set.quantity.value == 4


def test_validation_keeps_a_missing_tread_depth_missing_without_inventing_it() -> None:
    payload = _payload()
    tire_set = _tire_set(payload)
    tire_set["tires"]["value"][0]["tread_depth_mm"] = _field(None, "missing")  # type: ignore[index]

    validated = validate_extraction_payload(payload)

    assert validated["tire_sets"]["value"][0]["tire_set"]["tires"]["value"][0][  # type: ignore[index]
        "tread_depth_mm"
    ] == _field(None, "missing")
    assert validated["review_required"] is False


def test_validation_marks_hard_format_and_range_errors_invalid() -> None:
    payload = _payload()
    payload["vehicle"]["license_plate"] = _field("CW-ABC 123")  # type: ignore[index]
    payload["vehicle"]["mileage_km"] = _field(-1)  # type: ignore[index]
    tire_set = _tire_set(payload)
    tire_set["width_mm"] = _field(123)
    tire_set["aspect_ratio"] = _field(54)
    tire_set["rim_diameter_inch"] = _field(9)
    tire_set["quantity"] = _field(9)
    tire_set["tires"]["value"][0]["position"] = _field("front")  # type: ignore[index]
    tire_set["tires"]["value"][0]["tread_depth_mm"] = _field(20.0)  # type: ignore[index]

    validated = validate_extraction_payload(payload)
    validated_tire_set = _tire_set(validated)

    assert validated["vehicle"]["license_plate"]["field_status"] == "invalid"  # type: ignore[index]
    assert validated["vehicle"]["mileage_km"] == _field(-1, "invalid")  # type: ignore[index]
    for name in ("width_mm", "aspect_ratio", "rim_diameter_inch", "quantity"):
        assert validated_tire_set[name]["field_status"] == "invalid"
    assert validated_tire_set["tires"]["value"][0]["position"]["field_status"] == "invalid"  # type: ignore[index]
    assert validated_tire_set["tires"]["value"][0]["tread_depth_mm"]["field_status"] == "invalid"  # type: ignore[index]
    assert validated["review_required"] is True


def test_validation_preserves_uncertainty_and_marks_unknown_or_conflicts_uncertain() -> None:
    payload = _payload()
    tire_set = _tire_set(payload)
    tire_set["tire_type"] = _field("unknown")
    tire_set["model"] = _field(None, "uncertain")
    tire_set["tires"]["value"][1]["position"] = _field("front_left")  # type: ignore[index]
    payload["vehicle"]["model"] = _field("unbekannt")  # type: ignore[index]
    payload["conditions"]["value"][0]["condition"] = _field("unknown")  # type: ignore[index]

    conflicting_inspection = deepcopy(payload["tire_inspections"]["value"][0])  # type: ignore[index]
    conflicting_inspection["tread_front_mm"] = _field(4.0)
    payload["tire_inspections"]["value"].append(conflicting_inspection)  # type: ignore[index]

    validated = validate_extraction_payload(payload)
    validated_tire_set = _tire_set(validated)

    assert validated_tire_set["tire_type"] == _field(None, "uncertain")
    assert validated_tire_set["model"] == _field(None, "uncertain")
    assert validated["vehicle"]["model"] == _field(None, "uncertain")  # type: ignore[index]
    assert validated["conditions"]["value"][0]["condition"] == _field(None, "uncertain")  # type: ignore[index]
    assert validated_tire_set["tires"]["value"][0]["position"] == _field(None, "uncertain")  # type: ignore[index]
    assert validated_tire_set["tires"]["value"][1]["position"] == _field(None, "uncertain")  # type: ignore[index]
    assert validated["tire_inspections"]["value"][0]["tread_front_mm"] == _field(None, "uncertain")  # type: ignore[index]
    assert validated["tire_inspections"]["value"][1]["tread_front_mm"] == _field(None, "uncertain")  # type: ignore[index]
    assert validated["review_required"] is True


def test_response_boundary_validates_after_normalization_without_completing_fields() -> None:
    payload = _payload()
    payload["vehicle"]["license_plate"] = _field("cw ab123")  # type: ignore[index]
    payload["vehicle"]["mileage_km"] = _field("-1 Kilometer")  # type: ignore[index]
    tire_set = _tire_set(payload)
    tire_set["manufacturer"] = _field("Conti")
    tire_set["model"] = _field(None, "uncertain")

    result = normalize_and_validate_extraction_response(payload)

    assert result.vehicle.license_plate.value == "CW-AB 123"
    assert result.vehicle.mileage_km.value == -1
    assert result.vehicle.mileage_km.field_status.value == "invalid"
    assert result.tire_sets.value is not None
    validated_tire_set = result.tire_sets.value[0].tire_set
    assert validated_tire_set.manufacturer.value == "Continental"
    assert validated_tire_set.model.value is None
    assert validated_tire_set.model.field_status.value == "uncertain"
    assert result.review_required is True
