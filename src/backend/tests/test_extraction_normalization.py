"""Unit tests for deterministic post-extraction value normalization."""

from __future__ import annotations

import pytest

from app.models.extraction import StructuredExtractionResult
from app.services.extraction import normalize_and_validate_extraction_response
from app.services.extraction_normalization import (
    normalize_extraction_payload,
    normalize_license_plate,
    normalize_mileage_km,
    normalize_quantity,
    normalize_structured_extraction_result,
    normalize_tire_position,
    normalize_tire_size,
    normalize_tread_depth_mm,
    parse_tire_size,
)


def _field(value: object, field_status: str = "valid") -> dict[str, object]:
    return {"value": value, "field_status": field_status}


def _missing(*names: str) -> dict[str, dict[str, object]]:
    return {name: _field(None, "missing") for name in names}


def _payload() -> dict[str, object]:
    return {
        "service_type": _field("tire_storage"),
        "service_date": _field(None, "missing"),
        "vehicle": {
            "license_plate": _field("cw ab123"),
            "mileage_km": _field("63.500 Kilometer"),
            "make": _field("  Ford  "),
            "model": _field("  Focus   Turnier "),
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
                        "tire_type": _field("Allwetterreifen"),
                        "width_mm": _field("225"),
                        "aspect_ratio": _field("45"),
                        "rim_diameter_inch": _field("17"),
                        **_missing(
                            "rim_category",
                            "rim_manufacturer",
                            "rim_model",
                        ),
                        "manufacturer": _field(" conti "),
                        "model": _field(" WinterContact   TS 870 "),
                        "quantity": _field("vier"),
                        **_missing(
                            "dot",
                            "load_index",
                            "speed_index",
                            "notes",
                        ),
                        "tires": _field(
                            [
                                {
                                    "position": _field("Vorderachse links"),
                                    "manufacturer": _field(" michelin "),
                                    "profile": _field(" Pilot   Sport 5 "),
                                    "tread_depth_mm": _field("4,5 Millimeter"),
                                    **_missing(
                                        "dot",
                                        "wear_marks_present",
                                        "has_damage",
                                        "damage_notes",
                                    ),
                                }
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
                    "tread_front_mm": _field("5,0 mm"),
                    "tread_rear_mm": _field("vier"),
                    "notes": _field(None, "missing"),
                }
            ]
        ),
        "conditions": _field(
            [
                {
                    "tire_set_role": _field("stored"),
                    "condition": _field("worn"),
                    "position": _field("hinten rechts"),
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
                    "position": _field("vorne"),
                    "notes": _field(None, "missing"),
                }
            ]
        ),
        "tire_change_details": _field(None, "missing"),
        "review_required": False,
    }


def test_normalization_converts_supported_values_to_existing_typed_fields() -> None:
    normalized = normalize_extraction_payload(_payload())
    result = StructuredExtractionResult.model_validate(normalized)

    assert result.vehicle.license_plate.value == "CW-AB 123"
    assert result.vehicle.mileage_km.value == 63500
    assert result.vehicle.make.value == "Ford"
    assert result.vehicle.model.value == "Focus Turnier"

    tire_set = result.tire_sets.value[0].tire_set  # type: ignore[index,union-attr]
    assert tire_set.tire_type.value == "all_season"
    assert (tire_set.width_mm.value, tire_set.aspect_ratio.value, tire_set.rim_diameter_inch.value) == (225, 45, 17)
    assert tire_set.manufacturer.value == "Continental"
    assert tire_set.model.value == "WinterContact TS 870"
    assert tire_set.quantity.value == 4
    assert tire_set.tires.value[0].position.value == "front_left"  # type: ignore[index,union-attr]
    assert tire_set.tires.value[0].manufacturer.value == "Michelin"  # type: ignore[index,union-attr]
    assert tire_set.tires.value[0].profile.value == "Pilot Sport 5"  # type: ignore[index,union-attr]
    assert tire_set.tires.value[0].tread_depth_mm.value == 4.5  # type: ignore[index,union-attr]

    inspection = result.tire_inspections.value[0]  # type: ignore[index,union-attr]
    assert inspection.tread_front_mm.value == 5.0
    assert inspection.tread_rear_mm.value == 4.0
    assert result.conditions.value[0].position.value == "rear_right"  # type: ignore[index,union-attr]
    assert result.visual_inspections.value[0].position.value == "front"  # type: ignore[index,union-attr]
    assert result.review_required is False


@pytest.mark.parametrize(
    ("spoken", "expected"),
    [
        ("225 45 17", "225/45 R17"),
        ("225/45 R17", "225/45 R17"),
        ("225/45R17", "225/45 R17"),
        ("225/45 ZR17", "225/45 R17"),
        ("225 durch 45 auf 17", "225/45 R17"),
        ("225 slash 45 R 17", "225/45 R17"),
        ("225, 45, 17.", "225/45 R17"),
        ("zweihundertfünfundzwanzig fünfundvierzig siebzehn", "225/45 R17"),
    ],
)
def test_tire_size_variants_have_one_canonical_representation(
    spoken: str, expected: str
) -> None:
    size = parse_tire_size(spoken)

    assert size is not None
    assert size.canonical == expected
    assert normalize_tire_size(spoken) == expected


def test_spoken_numeric_values_are_stored_as_numbers_without_defaults() -> None:
    assert normalize_mileage_km("73 tausend 400 Kilometer") == 73400
    assert normalize_quantity("also vier Reifen") == 4
    assert normalize_tread_depth_mm("äh vier komma null fünf Millimeter.") == 4.05


def test_spoken_plate_digits_are_normalized_only_with_clear_letter_groups() -> None:
    assert normalize_license_plate("CW AB eins zwo drei.") == "CW-AB 123"
    assert normalize_license_plate("CW AB 123.") == "CW-AB 123"
    assert normalize_license_plate("C W A B eins zwei drei") is None


@pytest.mark.parametrize(
    ("spoken", "expected"),
    [
        ("vorne links", "front_left"),
        ("linke Vorderachse", "front_left"),
        ("Vorderachse rechts", "front_right"),
        ("ähm Vorderachse, links", "front_left"),
        ("hinten links", "rear_left"),
        ("rechte Hinterachse", "rear_right"),
        ("Vorderachse", "front"),
        ("hinten", "rear"),
    ],
)
def test_positions_and_axles_normalize_to_documented_enum_values(
    spoken: str, expected: str
) -> None:
    assert normalize_tire_position(spoken) == expected


def test_unknown_valid_values_are_downgraded_without_promoting_marked_values() -> None:
    payload = _payload()
    vehicle = payload["vehicle"]  # type: ignore[assignment]
    vehicle["license_plate"] = _field("not a plate")
    vehicle["model"] = _field(None, "uncertain")
    tire_set = payload["tire_sets"]["value"][0]["tire_set"]  # type: ignore[index]
    tire_set["tire_type"] = _field("Offroadreifen")
    tire_set["aspect_ratio"] = _field(None, "missing")
    tire_set["tires"]["value"][0]["position"] = _field("links")  # type: ignore[index]

    normalized = normalize_extraction_payload(payload)
    normalized_vehicle = normalized["vehicle"]
    normalized_tire_set = normalized["tire_sets"]["value"][0]["tire_set"]  # type: ignore[index]

    assert normalized_vehicle["license_plate"] == _field("not a plate", "invalid")
    assert normalized_vehicle["model"] == _field(None, "uncertain")
    assert normalized_tire_set["tire_type"] == _field(None, "uncertain")
    assert normalized_tire_set["aspect_ratio"] == _field(None, "missing")
    assert normalized_tire_set["tires"]["value"][0]["position"] == _field(  # type: ignore[index]
        None, "uncertain"
    )
    assert normalized["review_required"] is True


def test_marked_invalid_values_are_never_reinterpreted_as_valid() -> None:
    payload = _payload()
    tire_set = payload["tire_sets"]["value"][0]["tire_set"]  # type: ignore[index]
    tire_set["manufacturer"] = _field("Conti", "invalid")

    normalized = normalize_extraction_payload(payload)
    manufacturer = normalized["tire_sets"]["value"][0]["tire_set"]["manufacturer"]  # type: ignore[index]

    assert manufacturer == _field("Conti", "invalid")
    assert normalized["review_required"] is True


def test_missing_or_uncertain_model_placeholders_are_cleared_before_validation() -> None:
    payload = _payload()
    tire = payload["tire_sets"]["value"][0]["tire_set"]["tires"]["value"][0]  # type: ignore[index]
    tire["position"] = _field("front_left", "missing")
    payload["tire_inspections"] = _field([], "missing")
    payload["visual_inspections"] = _field([], "uncertain")

    normalized = normalize_extraction_payload(payload)
    result = StructuredExtractionResult.model_validate(normalized)

    normalized_tire = normalized["tire_sets"]["value"][0]["tire_set"]["tires"]["value"][0]  # type: ignore[index]
    assert normalized_tire["position"] == _field(None, "missing")
    assert normalized["tire_inspections"] == _field(None, "missing")
    assert normalized["visual_inspections"] == _field(None, "uncertain")
    assert result.review_required is True


def test_typed_normalization_returns_a_new_schema_valid_result() -> None:
    raw = _payload()
    raw["vehicle"]["license_plate"] = _field("cw-ab 123")  # type: ignore[index]
    result = StructuredExtractionResult.model_validate(normalize_extraction_payload(raw))

    normalized = normalize_structured_extraction_result(result)

    assert normalized is not result
    assert normalized.vehicle.license_plate.value == "CW-AB 123"


def test_ai_response_boundary_normalizes_before_schema_validation() -> None:
    result = normalize_and_validate_extraction_response(_payload())

    assert result.vehicle.mileage_km.value == 63500
    assert result.tire_sets.value[0].tire_set.quantity.value == 4  # type: ignore[index,union-attr]
