"""Strict Structured-Output contract for AI-assisted workshop extraction.

This module deliberately does not reuse the editable registration draft.  An
LLM response must state both the value and its extraction status for every
field, while a mechanic draft may still omit values during manual entry.  The
result can therefore be validated directly after a Structured Outputs response
without guessing missing values or changing the established domain models.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Generic, Iterator, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import (
    FieldStatus,
    InspectionResult,
    PropulsionType,
    RdksType,
    RimCategory,
    ServiceType,
    TireConditionType,
    TirePosition,
    TireSetRole,
    TireType,
    VisualInspectionComponent,
    VisualInspectionResult,
    WheelBoltConfiguration,
)
from app.models.schemas import YearMonth


T = TypeVar("T")


class StructuredExtractionModel(BaseModel):
    """Base policy required by JSON Schema Structured Outputs.

    ``extra='forbid'`` emits ``additionalProperties: false`` for every object,
    so responses cannot silently contain invented or misspelled fields.
    Fields intentionally have no defaults: nullable values remain required in
    the JSON Schema and must be returned explicitly as ``null`` when unknown.
    """

    model_config = ConfigDict(extra="forbid")


class ExtractedField(StructuredExtractionModel, Generic[T]):
    """One extracted value and the status assigned to that exact field."""

    value: Optional[T] = Field(
        description=(
            "Extracted value. It is null when the spoken information is missing "
            "or uncertain; no value may be inferred from surrounding context."
        )
    )
    field_status: FieldStatus = Field(
        description=(
            "Extraction status for value: valid, uncertain, missing, or invalid."
        )
    )

    @model_validator(mode="after")
    def keep_unknown_values_null(self) -> "ExtractedField[T]":
        """Prevent a status from masking a guessed value.

        ``invalid`` intentionally retains the explicitly spoken value so a
        later validation/review step can see what was said.  A valid value may
        also be the documented enum value ``unknown`` when that value itself
        was explicitly stated by the extraction rules.
        """

        if self.field_status in {FieldStatus.MISSING, FieldStatus.UNCERTAIN}:
            if self.value is not None:
                raise ValueError(
                    "a missing or uncertain extracted field must have value null"
                )
        elif self.value is None:
            raise ValueError(
                "a valid or invalid extracted field must retain its explicit value"
            )
        return self


class VehicleExtraction(StructuredExtractionModel):
    """All extractable Vehicle fields from DATA_MODEL.md."""

    license_plate: ExtractedField[str]
    mileage_km: ExtractedField[int]
    make: ExtractedField[str]
    model: ExtractedField[str]
    propulsion_type: ExtractedField[PropulsionType]
    first_registration_month: ExtractedField[YearMonth]
    max_speed_kmh: ExtractedField[int]
    vin: ExtractedField[str]


class TireExtraction(StructuredExtractionModel):
    """Per-wheel Tire values used by tire-storage extraction."""

    position: ExtractedField[TirePosition]
    manufacturer: ExtractedField[str]
    profile: ExtractedField[str]
    tread_depth_mm: ExtractedField[float]
    dot: ExtractedField[str]
    wear_marks_present: ExtractedField[bool]
    has_damage: ExtractedField[bool]
    damage_notes: ExtractedField[str]


class TireSetExtraction(StructuredExtractionModel):
    """All extractable TireSet fields, including stored individual tires."""

    tire_type: ExtractedField[TireType]
    width_mm: ExtractedField[int]
    aspect_ratio: ExtractedField[int]
    rim_diameter_inch: ExtractedField[int]
    rim_category: ExtractedField[RimCategory]
    rim_manufacturer: ExtractedField[str]
    rim_model: ExtractedField[str]
    manufacturer: ExtractedField[str]
    model: ExtractedField[str]
    quantity: ExtractedField[int]
    dot: ExtractedField[str]
    load_index: ExtractedField[str]
    speed_index: ExtractedField[str]
    notes: ExtractedField[str]
    tires: ExtractedField[List[TireExtraction]]


class ServiceTireSetExtraction(StructuredExtractionModel):
    """One tire set with its explicitly extracted role in the service record."""

    role: ExtractedField[TireSetRole]
    tire_set: TireSetExtraction


class TireInspectionExtraction(StructuredExtractionModel):
    """Axle and per-position tread readings tied to one tire-set role."""

    tire_set_role: ExtractedField[TireSetRole]
    tread_front_left_mm: ExtractedField[float]
    tread_front_right_mm: ExtractedField[float]
    tread_rear_left_mm: ExtractedField[float]
    tread_rear_right_mm: ExtractedField[float]
    tread_front_mm: ExtractedField[float]
    tread_rear_mm: ExtractedField[float]
    notes: ExtractedField[str]


class TireConditionExtraction(StructuredExtractionModel):
    """One lossless tire-condition finding and its position."""

    tire_set_role: ExtractedField[TireSetRole]
    condition: ExtractedField[TireConditionType]
    position: ExtractedField[TirePosition]
    notes: ExtractedField[str]


class VisualInspectionExtraction(StructuredExtractionModel):
    """One extracted visual inspection for a tire-change tire set."""

    tire_set_role: ExtractedField[TireSetRole]
    component: ExtractedField[VisualInspectionComponent]
    result: ExtractedField[VisualInspectionResult]
    position: ExtractedField[TirePosition]
    notes: ExtractedField[str]


class BrakeDiscMeasurementExtraction(StructuredExtractionModel):
    """One brake-disc position and thickness from a tire-change protocol."""

    position: ExtractedField[TirePosition]
    thickness_mm: ExtractedField[float]


class TireChangeDetailsExtraction(StructuredExtractionModel):
    """All extractable TireChangeDetails fields from DATA_MODEL.md."""

    wheel_change_performed: ExtractedField[bool]
    balancing_steel_count: ExtractedField[int]
    balancing_alloy_count: ExtractedField[int]
    machine_wash_count: ExtractedField[int]
    manual_wash_count: ExtractedField[int]
    whm_mode: ExtractedField[str]
    next_customer_service: ExtractedField[str]
    next_oil_service: ExtractedField[str]
    air_pressure_front_bar: ExtractedField[float]
    air_pressure_rear_bar: ExtractedField[float]
    wheel_lock_present: ExtractedField[bool]
    wheel_bolt_configuration: ExtractedField[WheelBoltConfiguration]
    hu_due_month: ExtractedField[YearMonth]
    suspension_visual_result: ExtractedField[InspectionResult]
    brake_visual_result: ExtractedField[InspectionResult]
    hub_cleaned: ExtractedField[bool]
    rdks_type: ExtractedField[RdksType]
    rdks_programmed: ExtractedField[bool]
    speed_limiter_set: ExtractedField[bool]
    speed_limiter_sticker_applied: ExtractedField[bool]
    wheel_bolt_torque_nm: ExtractedField[float]
    whatsapp_contact_allowed: ExtractedField[bool]
    brake_disc_measurements: ExtractedField[List[BrakeDiscMeasurementExtraction]]


def _iter_field_statuses(value: object) -> Iterator[FieldStatus]:
    """Yield statuses from nested typed extraction data only."""

    if isinstance(value, ExtractedField):
        yield value.field_status
        if value.value is not None:
            yield from _iter_field_statuses(value.value)
    elif isinstance(value, BaseModel):
        for field_name in value.__class__.model_fields:
            if field_name != "review_required":
                yield from _iter_field_statuses(getattr(value, field_name))
    elif isinstance(value, list):
        for item in value:
            yield from _iter_field_statuses(item)


class StructuredExtractionResult(StructuredExtractionModel):
    """Complete AI extraction result ready for an LLM Structured Output.

    The result contains only fields that can be extracted from the workshop
    statement. Identifiers, customer assignment, confirmation, timestamps,
    delivery state, and the raw transcript remain outside this contract.
    """

    service_type: ExtractedField[ServiceType]
    service_date: ExtractedField[date]
    vehicle: VehicleExtraction
    notes: ExtractedField[str]
    tire_sets: ExtractedField[List[ServiceTireSetExtraction]]
    tire_inspections: ExtractedField[List[TireInspectionExtraction]]
    conditions: ExtractedField[List[TireConditionExtraction]]
    visual_inspections: ExtractedField[List[VisualInspectionExtraction]]
    tire_change_details: ExtractedField[TireChangeDetailsExtraction]
    review_required: bool = Field(
        description=(
            "True exactly when at least one nested field_status is uncertain "
            "or invalid."
        )
    )

    @model_validator(mode="after")
    def keep_review_requirement_consistent(self) -> "StructuredExtractionResult":
        expected_review_required = any(
            status in {FieldStatus.UNCERTAIN, FieldStatus.INVALID}
            for status in _iter_field_statuses(self)
        )
        if self.review_required is not expected_review_required:
            raise ValueError(
                "review_required must be true exactly for uncertain or invalid fields"
            )
        return self


def structured_extraction_json_schema() -> dict[str, Any]:
    """Return the strict JSON Schema for an LLM Structured Outputs request."""

    return StructuredExtractionResult.model_json_schema()


__all__ = [
    "BrakeDiscMeasurementExtraction",
    "ExtractedField",
    "ServiceTireSetExtraction",
    "StructuredExtractionResult",
    "StructuredExtractionModel",
    "TireChangeDetailsExtraction",
    "TireConditionExtraction",
    "TireExtraction",
    "TireInspectionExtraction",
    "TireSetExtraction",
    "VehicleExtraction",
    "VisualInspectionExtraction",
    "structured_extraction_json_schema",
]
