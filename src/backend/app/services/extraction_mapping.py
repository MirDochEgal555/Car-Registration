"""Map a validated extraction result into the established registration draft.

The structured LLM model is intentionally richer than the browser draft: each
value carries an extraction status.  This mapper copies only values already
present in that model and flattens those existing statuses to the path format
used by ``RegistrationDraft.field_status``.  It never chooses a role, fills a
missing value, or discards an invalid value that needs review.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from app.models.enums import FieldStatus
from app.models.extraction import ExtractedField, StructuredExtractionResult
from app.models.registration import (
    BrakeDiscMeasurementDraft,
    RegistrationDraft,
    RegistrationTireSet,
    TireChangeDetailsDraft,
    TireConditionDraft,
    TireDraft,
    TireInspectionDraft,
    TireSetDraft,
    VehicleDraft,
    VisualInspectionDraft,
)


_T = TypeVar("_T")


class ExtractionMappingError(ValueError):
    """Raised if provider data cannot be represented by the existing draft."""


def map_extraction_to_registration_draft(
    transcript: str,
    extraction: StructuredExtractionResult,
) -> RegistrationDraft:
    """Return the final editable internal draft for one validated transcript.

    Missing and uncertain wrappers map to ``None`` exactly as required by the
    extraction model.  Invalid wrappers intentionally keep their supplied
    typed value; their flattened field status makes the later review visible.
    """

    vehicle = extraction.vehicle
    return RegistrationDraft(
        service_type=_value(extraction.service_type),
        service_date=_value(extraction.service_date),
        vehicle=VehicleDraft(
            license_plate=_value(vehicle.license_plate),
            mileage_km=_value(vehicle.mileage_km),
            make=_value(vehicle.make),
            model=_value(vehicle.model),
            propulsion_type=_value(vehicle.propulsion_type),
            first_registration_month=_value(vehicle.first_registration_month),
            max_speed_kmh=_value(vehicle.max_speed_kmh),
            vin=_value(vehicle.vin),
        ),
        notes=_value(extraction.notes),
        raw_transcript=transcript,
        field_status=flatten_extraction_field_statuses(extraction),
        tire_sets=[
            _map_tire_set(relation, index)
            for index, relation in enumerate(_value(extraction.tire_sets) or [])
        ],
        tire_inspections=[
            TireInspectionDraft(
                tire_set_role=_value(inspection.tire_set_role),
                tread_front_left_mm=_value(inspection.tread_front_left_mm),
                tread_front_right_mm=_value(inspection.tread_front_right_mm),
                tread_rear_left_mm=_value(inspection.tread_rear_left_mm),
                tread_rear_right_mm=_value(inspection.tread_rear_right_mm),
                tread_front_mm=_value(inspection.tread_front_mm),
                tread_rear_mm=_value(inspection.tread_rear_mm),
                notes=_value(inspection.notes),
            )
            for inspection in _value(extraction.tire_inspections) or []
        ],
        conditions=[
            TireConditionDraft(
                tire_set_role=_value(condition.tire_set_role),
                condition=_value(condition.condition),
                position=_value(condition.position),
                notes=_value(condition.notes),
            )
            for condition in _value(extraction.conditions) or []
        ],
        visual_inspections=[
            VisualInspectionDraft(
                tire_set_role=_value(inspection.tire_set_role),
                component=_value(inspection.component),
                result=_value(inspection.result),
                position=_value(inspection.position),
                notes=_value(inspection.notes),
            )
            for inspection in _value(extraction.visual_inspections) or []
        ],
        tire_change_details=_map_tire_change_details(
            _value(extraction.tire_change_details)
        ),
    )


def flatten_extraction_field_statuses(
    extraction: StructuredExtractionResult,
) -> dict[str, FieldStatus]:
    """Expose every existing extraction status in API draft-path notation."""

    statuses: dict[str, FieldStatus] = {}
    _collect_field_statuses(extraction.model_dump(mode="python"), "", statuses)
    return statuses


def _map_tire_set(relation: Any, index: int) -> RegistrationTireSet:
    role = _value(relation.role)
    if role is None:
        raise ExtractionMappingError(
            f"Die Rolle für Reifensatz {index + 1} ist nicht eindeutig zuordenbar."
        )
    tire_set = relation.tire_set
    return RegistrationTireSet(
        role=role,
        tire_set=TireSetDraft(
            tire_type=_value(tire_set.tire_type),
            width_mm=_value(tire_set.width_mm),
            aspect_ratio=_value(tire_set.aspect_ratio),
            rim_diameter_inch=_value(tire_set.rim_diameter_inch),
            rim_category=_value(tire_set.rim_category),
            rim_manufacturer=_value(tire_set.rim_manufacturer),
            rim_model=_value(tire_set.rim_model),
            manufacturer=_value(tire_set.manufacturer),
            model=_value(tire_set.model),
            quantity=_value(tire_set.quantity),
            dot=_value(tire_set.dot),
            load_index=_value(tire_set.load_index),
            speed_index=_value(tire_set.speed_index),
            notes=_value(tire_set.notes),
            tires=[
                TireDraft(
                    position=_value(tire.position),
                    manufacturer=_value(tire.manufacturer),
                    profile=_value(tire.profile),
                    tread_depth_mm=_value(tire.tread_depth_mm),
                    dot=_value(tire.dot),
                    wear_marks_present=_value(tire.wear_marks_present),
                    has_damage=_value(tire.has_damage),
                    damage_notes=_value(tire.damage_notes),
                )
                for tire in _value(tire_set.tires) or []
            ],
        ),
    )


def _map_tire_change_details(details: Any) -> TireChangeDetailsDraft | None:
    if details is None:
        return None
    return TireChangeDetailsDraft(
        wheel_change_performed=_value(details.wheel_change_performed),
        balancing_steel_count=_value(details.balancing_steel_count),
        balancing_alloy_count=_value(details.balancing_alloy_count),
        machine_wash_count=_value(details.machine_wash_count),
        manual_wash_count=_value(details.manual_wash_count),
        whm_mode=_value(details.whm_mode),
        next_customer_service=_value(details.next_customer_service),
        next_oil_service=_value(details.next_oil_service),
        air_pressure_front_bar=_value(details.air_pressure_front_bar),
        air_pressure_rear_bar=_value(details.air_pressure_rear_bar),
        wheel_lock_present=_value(details.wheel_lock_present),
        wheel_bolt_configuration=_value(details.wheel_bolt_configuration),
        hu_due_month=_value(details.hu_due_month),
        suspension_visual_result=_value(details.suspension_visual_result),
        brake_visual_result=_value(details.brake_visual_result),
        hub_cleaned=_value(details.hub_cleaned),
        rdks_type=_value(details.rdks_type),
        rdks_programmed=_value(details.rdks_programmed),
        speed_limiter_set=_value(details.speed_limiter_set),
        speed_limiter_sticker_applied=_value(details.speed_limiter_sticker_applied),
        wheel_bolt_torque_nm=_value(details.wheel_bolt_torque_nm),
        whatsapp_contact_allowed=_value(details.whatsapp_contact_allowed),
        brake_disc_measurements=[
            BrakeDiscMeasurementDraft(
                position=_value(measurement.position),
                thickness_mm=_value(measurement.thickness_mm),
            )
            for measurement in _value(details.brake_disc_measurements) or []
        ],
    )


def _value(field: ExtractedField[_T]) -> _T | None:
    return field.value


def _collect_field_statuses(
    value: object,
    path: str,
    statuses: dict[str, FieldStatus],
) -> None:
    """Collect wrappers recursively without introducing new marker names."""

    if _is_field_wrapper(value):
        wrapper = value
        if path:
            statuses[path] = FieldStatus(wrapper["field_status"])
        _collect_field_statuses(wrapper["value"], path, statuses)
        return
    if isinstance(value, Mapping):
        for name, child in value.items():
            if name == "review_required":
                continue
            child_path = f"{path}.{name}" if path else str(name)
            _collect_field_statuses(child, child_path, statuses)
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}.{index}" if path else str(index)
            _collect_field_statuses(child, child_path, statuses)


def _is_field_wrapper(value: object) -> bool:
    return (
        isinstance(value, Mapping)
        and set(value) == {"value", "field_status"}
        and isinstance(value["field_status"], (FieldStatus, str))
    )


__all__ = [
    "ExtractionMappingError",
    "flatten_extraction_field_statuses",
    "map_extraction_to_registration_draft",
]
