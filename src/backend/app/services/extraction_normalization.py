"""Deterministic normalization for values returned by AI extraction.

The Structured Outputs schema deliberately separates a value from its
``field_status``.  This module is the one normalisation boundary immediately
after an AI response and before the response is validated or mapped to a
registration draft.  It only rewrites explicitly supplied representations;
it never derives a value from a vehicle database, another field, or an
implicit default.

The raw-payload entry point is intentionally separate from Pydantic parsing.
That means an adapter can mark an unnormalisable provider value as invalid for
review without accidentally letting Pydantic coerce it first.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, MutableMapping
from copy import deepcopy
from dataclasses import dataclass
import math
import re
from typing import Any, TypeVar

from app.models.enums import FieldStatus, TirePosition, TireType
from app.models.extraction import StructuredExtractionResult


_T = TypeVar("_T")

_SPACE_RE = re.compile(r"\s+")
_LICENSE_PLATE_PATTERNS = (
    re.compile(
        r"^([A-ZÄÖÜ]{1,3})\s*-\s*([A-Z]{1,2})[\s-]*(\d{1,4}[A-Z]?)$"
    ),
    re.compile(r"^([A-ZÄÖÜ]{1,3})\s+([A-Z]{1,2})\s*(\d{1,4}[A-Z]?)$"),
)
_MILEAGE_RE = re.compile(
    r"^([+-]?(?:\d{1,3}(?:[.\s]\d{3})+|\d+))\s*(?:km|kilometer)?$",
    re.IGNORECASE,
)
_TREAD_RE = re.compile(
    r"^([+-]?\d+(?:[,.]\d+)?)\s*(?:mm|millimeter)?$", re.IGNORECASE
)
_TIRE_SIZE_CONNECTOR_RE = re.compile(
    r"\b(?:slash|schrägstrich|durch|auf|radial|zoll)\b", re.IGNORECASE
)
_TIRE_SIZE_R_RE = re.compile(r"\b(?:z\s*)?r\s*(?=\d)", re.IGNORECASE)
_TIRE_SIZE_ATTACHED_R_RE = re.compile(r"(?<=\d)\s*z?r\s*(?=\d)", re.IGNORECASE)

_MANUFACTURER_ALIASES = {
    "conti": "Continental",
    "continental": "Continental",
    "michelin": "Michelin",
    "goodyear": "Goodyear",
    "bridgestone": "Bridgestone",
    "pirelli": "Pirelli",
    "hankook": "Hankook",
}
_TIRE_TYPE_ALIASES = {
    "winter": TireType.WINTER.value,
    "winterreifen": TireType.WINTER.value,
    "summer": TireType.SUMMER.value,
    "sommer": TireType.SUMMER.value,
    "sommerreifen": TireType.SUMMER.value,
    "all season": TireType.ALL_SEASON.value,
    "all_season": TireType.ALL_SEASON.value,
    "allseason": TireType.ALL_SEASON.value,
    "ganzjahresreifen": TireType.ALL_SEASON.value,
    "allwetterreifen": TireType.ALL_SEASON.value,
    "unknown": TireType.UNKNOWN.value,
    "unbekannt": TireType.UNKNOWN.value,
    "reifen": TireType.UNKNOWN.value,
}
_POSITION_ALIASES = {
    "front left": TirePosition.FRONT_LEFT.value,
    "front_left": TirePosition.FRONT_LEFT.value,
    "vorne links": TirePosition.FRONT_LEFT.value,
    "vorn links": TirePosition.FRONT_LEFT.value,
    "vorderachse links": TirePosition.FRONT_LEFT.value,
    "links vorne": TirePosition.FRONT_LEFT.value,
    "links vorn": TirePosition.FRONT_LEFT.value,
    "links vorderachse": TirePosition.FRONT_LEFT.value,
    "linke vorderachse": TirePosition.FRONT_LEFT.value,
    "front right": TirePosition.FRONT_RIGHT.value,
    "front_right": TirePosition.FRONT_RIGHT.value,
    "vorne rechts": TirePosition.FRONT_RIGHT.value,
    "vorn rechts": TirePosition.FRONT_RIGHT.value,
    "vorderachse rechts": TirePosition.FRONT_RIGHT.value,
    "rechts vorne": TirePosition.FRONT_RIGHT.value,
    "rechts vorn": TirePosition.FRONT_RIGHT.value,
    "rechts vorderachse": TirePosition.FRONT_RIGHT.value,
    "rechte vorderachse": TirePosition.FRONT_RIGHT.value,
    "rear left": TirePosition.REAR_LEFT.value,
    "rear_left": TirePosition.REAR_LEFT.value,
    "hinten links": TirePosition.REAR_LEFT.value,
    "hinterachse links": TirePosition.REAR_LEFT.value,
    "links hinten": TirePosition.REAR_LEFT.value,
    "links hinterachse": TirePosition.REAR_LEFT.value,
    "linke hinterachse": TirePosition.REAR_LEFT.value,
    "rear right": TirePosition.REAR_RIGHT.value,
    "rear_right": TirePosition.REAR_RIGHT.value,
    "hinten rechts": TirePosition.REAR_RIGHT.value,
    "hinterachse rechts": TirePosition.REAR_RIGHT.value,
    "rechts hinten": TirePosition.REAR_RIGHT.value,
    "rechts hinterachse": TirePosition.REAR_RIGHT.value,
    "rechte hinterachse": TirePosition.REAR_RIGHT.value,
    "front": TirePosition.FRONT.value,
    "vorne": TirePosition.FRONT.value,
    "vorn": TirePosition.FRONT.value,
    "vorderachse": TirePosition.FRONT.value,
    "rear": TirePosition.REAR.value,
    "hinten": TirePosition.REAR.value,
    "hinterachse": TirePosition.REAR.value,
    "all": TirePosition.ALL.value,
    "alle": TirePosition.ALL.value,
    "unknown": TirePosition.UNKNOWN.value,
    "unbekannt": TirePosition.UNKNOWN.value,
}
_NUMBER_WORDS = {
    "null": 0,
    "ein": 1,
    "eins": 1,
    "eine": 1,
    "einen": 1,
    "einem": 1,
    "zwei": 2,
    "drei": 3,
    "vier": 4,
    "fünf": 5,
    "sechs": 6,
    "sieben": 7,
    "acht": 8,
    "neun": 9,
    "zehn": 10,
    "elf": 11,
    "zwölf": 12,
    "dreizehn": 13,
    "vierzehn": 14,
    "fünfzehn": 15,
    "sechzehn": 16,
    "siebzehn": 17,
    "achtzehn": 18,
    "neunzehn": 19,
    "zwanzig": 20,
    "dreißig": 30,
    "vierzig": 40,
    "fünfzig": 50,
    "sechzig": 60,
    "siebzig": 70,
    "achtzig": 80,
    "neunzig": 90,
}
_TENS = tuple(
    (word, number)
    for word, number in _NUMBER_WORDS.items()
    if number in {20, 30, 40, 50, 60, 70, 80, 90}
)
_HALF_NUMBER_WORDS = {
    "einhalb": 0.5,
    "eineinhalb": 1.5,
    "anderthalb": 1.5,
    "zweieinhalb": 2.5,
    "dreieinhalb": 3.5,
    "viereinhalb": 4.5,
    "fünfeinhalb": 5.5,
    "sechseinhalb": 6.5,
    "siebeneinhalb": 7.5,
    "achteinhalb": 8.5,
    "neuneinhalb": 9.5,
    "zehneinhalb": 10.5,
}


@dataclass(frozen=True)
class TireSize:
    """One complete tire size in the application's three existing fields."""

    width_mm: int
    aspect_ratio: int
    rim_diameter_inch: int

    @property
    def canonical(self) -> str:
        """Return the display form used consistently at system boundaries."""

        return f"{self.width_mm}/{self.aspect_ratio} R{self.rim_diameter_inch}"


def normalize_license_plate(value: object) -> str | None:
    """Return ``AA-BB 123`` only when its three supplied parts are unambiguous."""

    if not isinstance(value, str):
        return None
    candidate = _collapse_whitespace(value).upper()
    for pattern in _LICENSE_PLATE_PATTERNS:
        match = pattern.fullmatch(candidate)
        if match:
            district, letters, number = match.groups()
            return f"{district}-{letters} {number}"
    return None


def normalize_mileage_km(value: object) -> int | None:
    """Normalize an explicit kilometre value to one integer in kilometres."""

    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if math.isfinite(value) and value.is_integer() else None
    if not isinstance(value, str):
        return None
    match = _MILEAGE_RE.fullmatch(_collapse_whitespace(value))
    if match:
        return int(match.group(1).replace(".", "").replace(" ", ""))
    return _parse_spoken_mileage(value)


def normalize_tire_type(value: object) -> str | None:
    """Normalize only the explicitly supported German tire-type labels."""

    if isinstance(value, TireType):
        return value.value
    if not isinstance(value, str):
        return None
    key = _canonical_words(value)
    return _TIRE_TYPE_ALIASES.get(key)


def parse_tire_size(value: object) -> TireSize | None:
    """Parse a complete, explicitly supplied tire size without plausibility lookup.

    Digit variants such as ``225 45 17``, ``225/45 R17`` and ``225 durch 45
    auf 17`` are accepted.  The small German number-word parser also covers
    clear spoken components such as ``zweihundertfünfundzwanzig``.
    """

    if not isinstance(value, str):
        return None
    prepared = _TIRE_SIZE_CONNECTOR_RE.sub(" ", value.casefold())
    prepared = _TIRE_SIZE_R_RE.sub(" ", prepared)
    prepared = _TIRE_SIZE_ATTACHED_R_RE.sub(" ", prepared)
    prepared = re.sub(r"[/x×]", " ", prepared)
    parts = [part for part in _SPACE_RE.split(prepared.strip()) if part]
    if len(parts) != 3:
        return None
    numbers = [_parse_spoken_integer(part) for part in parts]
    if any(number is None for number in numbers):
        return None
    width_mm, aspect_ratio, rim_diameter_inch = (int(number) for number in numbers)
    return TireSize(width_mm, aspect_ratio, rim_diameter_inch)


def normalize_tire_size(value: object) -> str | None:
    """Return a complete tire size in the canonical ``225/45 R17`` form."""

    size = parse_tire_size(value)
    return size.canonical if size else None


def normalize_manufacturer(value: object) -> str | None:
    """Apply the documented tire-brand alias list and otherwise retain the name."""

    text = _normalize_text(value)
    if text is None:
        return None
    return _MANUFACTURER_ALIASES.get(text.casefold(), text)


def normalize_model(value: object) -> str | None:
    """Trim model spacing only; a model is never split from or copied to a make."""

    return _normalize_text(value)


def normalize_quantity(value: object) -> int | None:
    """Turn one explicit digit or German cardinal word into an integer."""

    if isinstance(value, str):
        text = _collapse_whitespace(value).casefold()
        for suffix in (" reifen", " stück"):
            if text.endswith(suffix):
                value = text[: -len(suffix)]
                break
    return _parse_spoken_integer(value)


def normalize_tread_depth_mm(value: object) -> float | None:
    """Normalize an explicit millimetre reading to a finite numeric value."""

    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if not isinstance(value, str):
        return None
    compact = _collapse_whitespace(value).casefold()
    if compact in _HALF_NUMBER_WORDS:
        return _HALF_NUMBER_WORDS[compact]
    match = _TREAD_RE.fullmatch(compact)
    if match:
        return float(match.group(1).replace(",", "."))
    spoken_decimal = _parse_spoken_decimal(compact)
    if spoken_decimal is not None:
        return spoken_decimal
    word_value = _parse_spoken_integer(compact)
    return float(word_value) if word_value is not None else None


def normalize_tire_position(value: object) -> str | None:
    """Map explicit axle/side wording to one documented ``TirePosition`` value."""

    if isinstance(value, TirePosition):
        return value.value
    if not isinstance(value, str):
        return None
    key = _canonical_words(value)
    return _POSITION_ALIASES.get(key)


def normalize_extraction_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a raw AI Structured-Output payload without mutating its input.

    Only fields currently marked ``valid`` are candidates.  Existing
    ``missing``, ``uncertain`` and ``invalid`` values are deliberately left
    byte-for-byte intact.  A valid but malformed free-text plate becomes
    ``invalid`` while retaining the text; malformed enum/numeric values become
    ``uncertain`` with ``null`` because the strict typed result cannot safely
    retain an incompatible scalar.
    """

    normalized = deepcopy(dict(payload))
    vehicle = _object(normalized.get("vehicle"))
    if vehicle is not None:
        _normalize_valid_field(
            vehicle,
            "license_plate",
            normalize_license_plate,
            retain_invalid_value=True,
        )
        _normalize_valid_field(vehicle, "mileage_km", normalize_mileage_km)
        _normalize_valid_field(vehicle, "make", normalize_model)
        _normalize_valid_field(vehicle, "model", normalize_model)

    for relation in _valid_list_value(normalized.get("tire_sets")):
        relation_object = _object(relation)
        if relation_object is None:
            continue
        tire_set = _object(relation_object.get("tire_set"))
        if tire_set is None:
            continue
        _normalize_tire_set(tire_set)

    for inspection in _valid_list_value(normalized.get("tire_inspections")):
        inspection_object = _object(inspection)
        if inspection_object is None:
            continue
        for name in (
            "tread_front_left_mm",
            "tread_front_right_mm",
            "tread_rear_left_mm",
            "tread_rear_right_mm",
            "tread_front_mm",
            "tread_rear_mm",
        ):
            _normalize_valid_field(
                inspection_object, name, normalize_tread_depth_mm
            )

    for collection_name in ("conditions", "visual_inspections"):
        for finding in _valid_list_value(normalized.get(collection_name)):
            finding_object = _object(finding)
            if finding_object is not None:
                _normalize_valid_field(
                    finding_object, "position", normalize_tire_position
                )

    details = _valid_object_value(normalized.get("tire_change_details"))
    if details is not None:
        for measurement in _valid_list_value(details.get("brake_disc_measurements")):
            measurement_object = _object(measurement)
            if measurement_object is not None:
                _normalize_valid_field(
                    measurement_object, "position", normalize_tire_position
                )

    normalized["review_required"] = _has_review_status(normalized)
    return normalized


def normalize_structured_extraction_result(
    result: StructuredExtractionResult,
) -> StructuredExtractionResult:
    """Normalize an already schema-valid result and return a new typed instance."""

    payload = normalize_extraction_payload(result.model_dump(mode="json"))
    return StructuredExtractionResult.model_validate(payload)


# A concise name for callers that already hold the Pydantic extraction model.
normalize_extraction_result = normalize_structured_extraction_result


def _normalize_tire_set(tire_set: MutableMapping[str, Any]) -> None:
    _normalize_valid_field(tire_set, "tire_type", normalize_tire_type)
    _normalize_tire_size_fields(tire_set)
    _normalize_valid_field(tire_set, "manufacturer", normalize_manufacturer)
    _normalize_valid_field(tire_set, "model", normalize_model)
    _normalize_valid_field(tire_set, "quantity", normalize_quantity)

    for tire in _valid_list_value(tire_set.get("tires")):
        tire_object = _object(tire)
        if tire_object is None:
            continue
        _normalize_valid_field(tire_object, "position", normalize_tire_position)
        _normalize_valid_field(tire_object, "manufacturer", normalize_manufacturer)
        _normalize_valid_field(tire_object, "profile", normalize_model)
        _normalize_valid_field(
            tire_object, "tread_depth_mm", normalize_tread_depth_mm
        )


def _normalize_tire_size_fields(tire_set: MutableMapping[str, Any]) -> None:
    """Normalize the three existing size fields without filling a missing field.

    The data model deliberately stores a size as three numeric fields.  A
    composite representation may be used only to verify a field that is
    already explicitly marked valid; no component is copied into a field that
    was marked missing, uncertain or invalid by extraction.
    """

    names = ("width_mm", "aspect_ratio", "rim_diameter_inch")
    fields = {name: _object(tire_set.get(name)) for name in names}
    parsed_sizes = [
        parse_tire_size(field.get("value"))
        for field in fields.values()
        if field is not None and _field_is_valid(field)
    ]
    complete_sizes = [size for size in parsed_sizes if size is not None]

    if complete_sizes:
        first_size = complete_sizes[0]
        if any(size != first_size for size in complete_sizes[1:]):
            for field in fields.values():
                _mark_uncertain(field)
            return
        expected = {
            "width_mm": first_size.width_mm,
            "aspect_ratio": first_size.aspect_ratio,
            "rim_diameter_inch": first_size.rim_diameter_inch,
        }
        for name, field in fields.items():
            if field is None or not _field_is_valid(field):
                continue
            parsed = parse_tire_size(field.get("value"))
            direct = _parse_spoken_integer(field.get("value"))
            if parsed is not None:
                field["value"] = expected[name]
            elif direct == expected[name]:
                field["value"] = direct
            else:
                _mark_uncertain(field)
        return

    for name, field in fields.items():
        if field is not None:
            _normalize_valid_field(fields, name, _parse_spoken_integer)


def _normalize_valid_field(
    container: MutableMapping[str, Any],
    name: str,
    normalizer: Callable[[object], _T | None],
    *,
    retain_invalid_value: bool = False,
) -> None:
    field = _object(container.get(name))
    if field is None or not _field_is_valid(field):
        return
    normalized = normalizer(field.get("value"))
    if normalized is not None:
        field["value"] = normalized
    elif retain_invalid_value:
        field["field_status"] = FieldStatus.INVALID.value
    else:
        _mark_uncertain(field)


def _mark_uncertain(field: MutableMapping[str, Any] | None) -> None:
    """Downgrade only a currently valid field that cannot be normalized safely."""

    if field is not None and _field_is_valid(field):
        field["value"] = None
        field["field_status"] = FieldStatus.UNCERTAIN.value


def _field_is_valid(field: Mapping[str, Any]) -> bool:
    return field.get("field_status") in {FieldStatus.VALID, FieldStatus.VALID.value}


def _valid_list_value(field: object) -> list[Any]:
    wrapper = _object(field)
    value = wrapper.get("value") if wrapper is not None and _field_is_valid(wrapper) else None
    return value if isinstance(value, list) else []


def _valid_object_value(field: object) -> MutableMapping[str, Any] | None:
    wrapper = _object(field)
    if wrapper is None or not _field_is_valid(wrapper):
        return None
    return _object(wrapper.get("value"))


def _object(value: object) -> MutableMapping[str, Any] | None:
    return value if isinstance(value, MutableMapping) else None


def _has_review_status(value: object) -> bool:
    if isinstance(value, Mapping):
        status = value.get("field_status")
        if status in {
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


def _normalize_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = _collapse_whitespace(value)
    return normalized or None


def _collapse_whitespace(value: str) -> str:
    return _SPACE_RE.sub(" ", value.strip())


def _canonical_words(value: str) -> str:
    return re.sub(r"[\s_-]+", " ", value.casefold()).strip()


def _parse_spoken_integer(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if math.isfinite(value) and value.is_integer() else None
    if not isinstance(value, str):
        return None
    compact = _collapse_whitespace(value).casefold()
    if re.fullmatch(r"[+-]?\d+", compact):
        return int(compact)
    return _parse_german_number_word(compact.replace(" ", ""))


def _parse_spoken_mileage(value: str) -> int | None:
    """Parse an explicit ``<number> tausend <number>`` kilometre expression."""

    text = _collapse_whitespace(value).casefold()
    text = re.sub(r"\s*(?:km|kilometer)$", "", text).strip()
    parts = text.split()
    if parts.count("tausend") != 1:
        return None
    separator = parts.index("tausend")
    if not parts[:separator] or not parts[separator + 1 :]:
        return None
    thousands = _parse_spoken_integer(" ".join(parts[:separator]))
    remainder = _parse_spoken_integer(" ".join(parts[separator + 1 :]))
    if thousands is None or remainder is None:
        return None
    return thousands * 1000 + remainder


def _parse_spoken_decimal(value: str) -> float | None:
    """Parse one explicit German ``x komma y`` millimetre reading."""

    text = re.sub(r"\s*(?:mm|millimeter)$", "", value).strip()
    parts = text.split(" komma ")
    if len(parts) != 2:
        return None
    whole = _parse_spoken_integer(parts[0])
    fraction = _parse_spoken_integer(parts[1])
    if whole is None or fraction is None or fraction < 0:
        return None
    return float(f"{whole}.{fraction}")


def _parse_german_number_word(value: str) -> int | None:
    direct = _NUMBER_WORDS.get(value)
    if direct is not None:
        return direct
    if "hundert" in value:
        prefix, suffix = value.split("hundert", maxsplit=1)
        hundreds = 1 if not prefix else _NUMBER_WORDS.get(prefix)
        remainder = 0 if not suffix else _parse_german_number_word(suffix)
        if hundreds is None or remainder is None:
            return None
        return hundreds * 100 + remainder
    for tens_word, tens_value in _TENS:
        if value.endswith(tens_word):
            unit_word = value[: -len(tens_word)]
            if unit_word.endswith("und"):
                unit = _NUMBER_WORDS.get(unit_word[:-3])
                if unit is not None and unit < 10:
                    return tens_value + unit
    return None


__all__ = [
    "TireSize",
    "normalize_extraction_payload",
    "normalize_extraction_result",
    "normalize_license_plate",
    "normalize_manufacturer",
    "normalize_mileage_km",
    "normalize_model",
    "normalize_quantity",
    "normalize_structured_extraction_result",
    "normalize_tire_position",
    "normalize_tire_size",
    "normalize_tire_type",
    "normalize_tread_depth_mm",
    "parse_tire_size",
]
