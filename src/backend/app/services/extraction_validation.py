"""Deterministic domain validation for normalized extraction results.

This is intentionally a separate boundary after
:mod:`app.services.extraction_normalization`.  Normalization converts clear
spoken representations to the application's existing types; this module only
checks their format and domain plausibility.  It never fills, derives, or
promotes extracted information.

``invalid`` is reserved for a supplied value that violates a hard format or
range rule.  ``uncertain`` is reserved for an unresolved meaning, such as an
explicit ``unknown`` value or two incompatible claims for one wheel position.
Both statuses require review, while pre-existing ``missing``, ``uncertain``,
and ``invalid`` values remain untouched.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from copy import deepcopy
import math
import re
from typing import Any

from app.models.enums import FieldStatus
from app.models.extraction import StructuredExtractionResult


_LICENSE_PLATE_PATTERN = re.compile(
    r"^[A-ZÄÖÜ]{1,3}-[A-Z]{1,2}\s\d{1,4}[A-Z]?$"
)

# The validation deliberately uses transparent passenger-car limits.  It does
# not query a vehicle, tyre, or manufacturer database.
_MILEAGE_MIN_KM = 0
_MILEAGE_MAX_KM = 2_000_000
_TIRE_QUANTITY_MIN = 1
_TIRE_QUANTITY_MAX = 8
_TIRE_WIDTH_MIN_MM = 125
_TIRE_WIDTH_MAX_MM = 405
_TIRE_ASPECT_RATIO_MIN = 20
_TIRE_ASPECT_RATIO_MAX = 95
_RIM_DIAMETER_MIN_INCH = 10
_RIM_DIAMETER_MAX_INCH = 24
_TREAD_DEPTH_MIN_MM = 0.0
_TREAD_DEPTH_MAX_MM = 15.0

_TREAD_FIELD_NAMES = (
    "tread_front_left_mm",
    "tread_front_right_mm",
    "tread_rear_left_mm",
    "tread_rear_right_mm",
    "tread_front_mm",
    "tread_rear_mm",
)
_CONCRETE_TIRE_POSITIONS = {
    "front_left",
    "front_right",
    "rear_left",
    "rear_right",
}
_NON_CONCRETE_TIRE_POSITIONS = {"front", "rear", "all"}
_UNKNOWN_MARKERS = {"unknown", "unbekannt"}


def validate_extraction_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate normalized extraction data without mutating the input.

    The function accepts the raw wrapper representation so it can run before
    Pydantic's final schema validation.  It only ever downgrades fields that
    were marked ``valid`` by extraction or normalization.  The returned
    payload is consequently still compatible with ``StructuredExtractionResult``
    whenever the normalized input was compatible.
    """

    validated = deepcopy(dict(payload))

    # An explicitly unknown domain value has not become known merely because
    # it passed through a normalizer.  This applies recursively to all field
    # wrappers except free-form notes, where the word can be literal text.
    _downgrade_unknown_markers(validated)

    vehicle = _object(validated.get("vehicle"))
    if vehicle is not None:
        _validate_license_plate(vehicle.get("license_plate"))
        _validate_integer_range(
            vehicle.get("mileage_km"),
            minimum=_MILEAGE_MIN_KM,
            maximum=_MILEAGE_MAX_KM,
        )

    service_type = _field_value(validated.get("service_type"))
    tire_set_roles: set[str] = set()
    tire_sets = _valid_list_value(validated.get("tire_sets"))
    for relation in tire_sets:
        relation_object = _object(relation)
        if relation_object is None:
            continue
        role_field = _object(relation_object.get("role"))
        role = _field_value(role_field)
        if isinstance(role, str):
            tire_set_roles.add(role)
        _validate_tire_set_role(role_field, service_type)

        tire_set = _object(relation_object.get("tire_set"))
        if tire_set is not None:
            _validate_tire_set(tire_set)

    _validate_tire_inspections(
        _valid_list_value(validated.get("tire_inspections")), tire_set_roles
    )
    _validate_conditions(
        _valid_list_value(validated.get("conditions")), tire_set_roles
    )
    _validate_visual_inspections(
        _valid_list_value(validated.get("visual_inspections")), tire_set_roles
    )

    validated["review_required"] = _has_review_status(validated)
    return validated


def validate_structured_extraction_result(
    result: StructuredExtractionResult,
) -> StructuredExtractionResult:
    """Validate a typed extraction result and return an independent copy."""

    payload = validate_extraction_payload(result.model_dump(mode="json"))
    return StructuredExtractionResult.model_validate(payload)


# Short alias for callers that already hold a typed result.
validate_extraction_result = validate_structured_extraction_result


def _validate_license_plate(field: object) -> None:
    value = _field_value(field)
    if not isinstance(value, str) or not _LICENSE_PLATE_PATTERN.fullmatch(value):
        _mark_invalid(_object(field))


def _validate_tire_set_role(field: MutableMapping[str, Any] | None, service_type: object) -> None:
    role = _field_value(field)
    if not isinstance(role, str):
        return
    if service_type == "tire_change" and role not in {"installed", "removed"}:
        _mark_invalid(field)
    elif service_type == "tire_storage" and role != "stored":
        _mark_invalid(field)


def _validate_tire_set(tire_set: MutableMapping[str, Any]) -> None:
    _validate_tire_size(tire_set)
    quantity_field = _object(tire_set.get("quantity"))
    _validate_integer_range(
        quantity_field,
        minimum=_TIRE_QUANTITY_MIN,
        maximum=_TIRE_QUANTITY_MAX,
    )

    tires_field = _object(tire_set.get("tires"))
    tires = _valid_list_value(tires_field)
    positions: dict[str, list[MutableMapping[str, Any]]] = {}
    for tire in tires:
        tire_object = _object(tire)
        if tire_object is None:
            continue
        position_field = _object(tire_object.get("position"))
        position = _field_value(position_field)
        if isinstance(position, str):
            if position not in _CONCRETE_TIRE_POSITIONS:
                _mark_invalid(position_field)
            elif _field_is_valid(position_field):
                positions.setdefault(position, []).append(position_field)
        _validate_tread_depth(tire_object.get("tread_depth_mm"))

    # A TireExtraction describes one physical tyre.  The same concrete
    # position twice is not a format error; it is an unresolved assignment.
    for duplicate_fields in positions.values():
        if len(duplicate_fields) > 1:
            for position_field in duplicate_fields:
                _mark_uncertain(position_field)

    quantity = _field_value(quantity_field)
    if isinstance(quantity, int) and not isinstance(quantity, bool):
        if len(tires) > quantity:
            _mark_invalid(quantity_field)


def _validate_tire_size(tire_set: MutableMapping[str, Any]) -> None:
    """Validate the existing width/aspect/rim fields as one tyre-size format."""

    width = _object(tire_set.get("width_mm"))
    aspect_ratio = _object(tire_set.get("aspect_ratio"))
    rim_diameter = _object(tire_set.get("rim_diameter_inch"))

    _validate_integer_range(
        width,
        minimum=_TIRE_WIDTH_MIN_MM,
        maximum=_TIRE_WIDTH_MAX_MM,
        step=5,
    )
    _validate_integer_range(
        aspect_ratio,
        minimum=_TIRE_ASPECT_RATIO_MIN,
        maximum=_TIRE_ASPECT_RATIO_MAX,
        step=5,
    )
    _validate_integer_range(
        rim_diameter,
        minimum=_RIM_DIAMETER_MIN_INCH,
        maximum=_RIM_DIAMETER_MAX_INCH,
    )


def _validate_tire_inspections(
    inspections: list[Any], tire_set_roles: set[str]
) -> None:
    readings: dict[tuple[str, str], list[MutableMapping[str, Any]]] = {}
    for inspection in inspections:
        inspection_object = _object(inspection)
        if inspection_object is None:
            continue
        role_field = _object(inspection_object.get("tire_set_role"))
        role = _field_value(role_field)
        if isinstance(role, str) and role not in tire_set_roles:
            _mark_invalid(role_field)

        for name in _TREAD_FIELD_NAMES:
            field = _object(inspection_object.get(name))
            _validate_tread_depth(field)
            value = _field_value(field)
            if isinstance(role, str) and _is_valid_tread_depth(value):
                readings.setdefault((role, name), []).append(field)  # type: ignore[arg-type]

    # Two different values for one set and one documented position/axle cannot
    # be resolved deterministically.  Preserve neither as confidently valid.
    for fields in readings.values():
        values = {_field_value(field) for field in fields}
        if len(values) > 1:
            for field in fields:
                _mark_uncertain(field)


def _validate_conditions(
    conditions: list[Any], tire_set_roles: set[str]
) -> None:
    for condition in conditions:
        condition_object = _object(condition)
        if condition_object is None:
            continue
        role_field = _object(condition_object.get("tire_set_role"))
        role = _field_value(role_field)
        if isinstance(role, str) and role not in tire_set_roles:
            _mark_invalid(role_field)


def _validate_visual_inspections(
    inspections: list[Any], tire_set_roles: set[str]
) -> None:
    for inspection in inspections:
        inspection_object = _object(inspection)
        if inspection_object is None:
            continue
        role_field = _object(inspection_object.get("tire_set_role"))
        role = _field_value(role_field)
        if isinstance(role, str) and role not in tire_set_roles:
            _mark_invalid(role_field)

        result = _field_value(inspection_object.get("result"))
        position_field = _object(inspection_object.get("position"))
        position = _field_value(position_field)
        if result == "not_ok" and position in _NON_CONCRETE_TIRE_POSITIONS:
            _mark_invalid(position_field)


def _validate_tread_depth(field: object) -> None:
    value = _field_value(field)
    if value is None:
        return
    if not _is_valid_tread_depth(value):
        _mark_invalid(_object(field))


def _is_valid_tread_depth(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    number = float(value)
    return (
        math.isfinite(number)
        and _TREAD_DEPTH_MIN_MM <= number <= _TREAD_DEPTH_MAX_MM
    )


def _validate_integer_range(
    field: object,
    *,
    minimum: int,
    maximum: int,
    step: int | None = None,
) -> None:
    value = _field_value(field)
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int):
        _mark_invalid(_object(field))
        return
    if value < minimum or value > maximum or (step is not None and value % step):
        _mark_invalid(_object(field))


def _downgrade_unknown_markers(value: object, *, field_name: str | None = None) -> None:
    """Turn a valid explicit unknown into uncertainty, never into validity."""

    if isinstance(value, MutableMapping):
        if field_name != "notes" and _field_is_valid(value):
            if _is_unknown_marker(value.get("value")):
                _mark_uncertain(value)
        for name, child in value.items():
            if name != "field_status":
                _downgrade_unknown_markers(child, field_name=name)
    elif isinstance(value, list):
        for item in value:
            _downgrade_unknown_markers(item, field_name=field_name)


def _is_unknown_marker(value: object) -> bool:
    enum_value = getattr(value, "value", value)
    return isinstance(enum_value, str) and enum_value.casefold() in _UNKNOWN_MARKERS


def _field_is_valid(field: Mapping[str, Any] | None) -> bool:
    return field is not None and field.get("field_status") in {
        FieldStatus.VALID,
        FieldStatus.VALID.value,
    }


def _field_value(field: object) -> Any | None:
    field_object = _object(field)
    return field_object.get("value") if _field_is_valid(field_object) else None


def _mark_invalid(field: MutableMapping[str, Any] | None) -> None:
    if _field_is_valid(field):
        field["field_status"] = FieldStatus.INVALID.value


def _mark_uncertain(field: MutableMapping[str, Any] | None) -> None:
    if _field_is_valid(field):
        field["value"] = None
        field["field_status"] = FieldStatus.UNCERTAIN.value


def _valid_list_value(field: object) -> list[Any]:
    value = _field_value(field)
    return value if isinstance(value, list) else []


def _object(value: object) -> MutableMapping[str, Any] | None:
    return value if isinstance(value, MutableMapping) else None


def _has_review_status(value: object) -> bool:
    if isinstance(value, Mapping):
        if value.get("field_status") in {
            FieldStatus.UNCERTAIN,
            FieldStatus.UNCERTAIN.value,
            FieldStatus.INVALID,
            FieldStatus.INVALID.value,
        }:
            return True
        return any(_has_review_status(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_review_status(item) for item in value)
    return False


__all__ = [
    "validate_extraction_payload",
    "validate_extraction_result",
    "validate_structured_extraction_result",
]
