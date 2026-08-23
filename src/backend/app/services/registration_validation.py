"""Business validation for client-owned registration drafts."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
import re
from typing import Callable

from app.models.enums import (
    FieldStatus,
    InspectionResult,
    ServiceType,
    TirePosition,
    TireSetRole,
    VisualInspectionResult,
)
from app.models.registration import RegistrationDraft, ValidationIssue, ValidationResponse
from app.models.review import calculate_review_required


_LICENSE_PLATE_PATTERN = re.compile(
    r"^[A-ZÄÖÜ]{1,3}-[A-Z]{1,2}\s?\d{1,4}[A-Z]?$"
)
_NON_CONCRETE_POSITIONS = {
    TirePosition.ALL,
    TirePosition.FRONT,
    TirePosition.REAR,
    TirePosition.UNKNOWN,
}
_TREAD_FIELDS = (
    "tread_front_left_mm",
    "tread_front_right_mm",
    "tread_rear_left_mm",
    "tread_rear_right_mm",
    "tread_front_mm",
    "tread_rear_mm",
)
IssueAdder = Callable[[str, str, str, FieldStatus], None]


def normalize_license_plate(value: str) -> str:
    """Normalize an explicitly supplied German-style plate without inventing text."""

    parts = [part for part in re.split(r"[-\s]+", value.strip().upper()) if part]
    if len(parts) >= 3:
        return f"{parts[0]}-{parts[1]} {''.join(parts[2:])}"
    if len(parts) == 2:
        return f"{parts[0]}-{parts[1]}"
    return value.strip().upper()


def validate_registration(draft: RegistrationDraft) -> ValidationResponse:
    """Validate workflow rules without persisting a draft or correcting values."""

    draft = draft.model_copy(deep=True)
    if draft.vehicle.license_plate:
        draft.vehicle.license_plate = normalize_license_plate(draft.vehicle.license_plate)
    field_status = dict(draft.field_status)
    issues: list[ValidationIssue] = []

    def add_issue(
        field: str,
        code: str,
        message: str,
        status: FieldStatus,
    ) -> None:
        issues.append(
            ValidationIssue(field=field, code=code, message=message, status=status)
        )
        existing = field_status.get(field)
        if existing is not FieldStatus.INVALID:
            field_status[field] = status

    if draft.service_type is None:
        add_issue(
            "service_type",
            "required",
            "Der Protokolltyp fehlt.",
            FieldStatus.MISSING,
        )
    if draft.service_date is None:
        add_issue(
            "service_date",
            "required",
            "Das Protokolldatum fehlt.",
            FieldStatus.MISSING,
        )
    elif draft.service_date > date.today():
        add_issue(
            "service_date",
            "future_date",
            "Das Protokolldatum darf nicht in der Zukunft liegen.",
            FieldStatus.INVALID,
        )
    if draft.mechanic_id is None:
        add_issue(
            "mechanic_id",
            "required",
            "Der erfassende Mechaniker fehlt.",
            FieldStatus.MISSING,
        )

    plate = draft.vehicle.license_plate
    if not plate:
        add_issue(
            "vehicle.license_plate",
            "required",
            "Das Kennzeichen fehlt.",
            FieldStatus.MISSING,
        )
    elif not _LICENSE_PLATE_PATTERN.fullmatch(normalize_license_plate(plate)):
        add_issue(
            "vehicle.license_plate",
            "invalid_format",
            "Das Kennzeichen hat kein plausibles Format.",
            FieldStatus.INVALID,
        )

    if draft.vehicle.mileage_km is not None and draft.vehicle.mileage_km < 0:
        add_issue(
            "vehicle.mileage_km",
            "negative_value",
            "Der Kilometerstand darf nicht negativ sein.",
            FieldStatus.INVALID,
        )
    if draft.vehicle.max_speed_kmh is not None and draft.vehicle.max_speed_kmh <= 0:
        add_issue(
            "vehicle.max_speed_kmh",
            "non_positive_value",
            "Die Höchstgeschwindigkeit muss größer als null sein.",
            FieldStatus.INVALID,
        )

    _validate_tire_sets(draft, add_issue)
    _validate_tire_inspections(draft, add_issue)
    _validate_visual_inspections(draft, add_issue)
    _validate_tire_change_details(draft, add_issue)

    # Keep a supplied uncertainty visible even if no local business rule found it.
    review_required = calculate_review_required(field_status)
    valid = not any(
        issue.status in {FieldStatus.MISSING, FieldStatus.INVALID} for issue in issues
    )
    return ValidationResponse(
        registration=draft,
        valid=valid,
        review_required=review_required,
        field_status=field_status,
        issues=issues,
    )


def _validate_tire_sets(draft: RegistrationDraft, add_issue: IssueAdder) -> None:
    """Validate role preservation and elementary tire-set plausibility."""

    allowed_roles = (
        {TireSetRole.INSTALLED, TireSetRole.REMOVED}
        if draft.service_type is ServiceType.TIRE_CHANGE
        else {TireSetRole.STORED}
        if draft.service_type is ServiceType.TIRE_STORAGE
        else set()
    )
    for index, relation in enumerate(draft.tire_sets):
        prefix = f"tire_sets.{index}"
        if allowed_roles and relation.role not in allowed_roles:
            add_issue(
                f"{prefix}.role",
                "invalid_role",
                "Die Reifensatzrolle passt nicht zum gewählten Protokolltyp.",
                FieldStatus.INVALID,
            )
        tire_set = relation.tire_set
        _validate_range(
            add_issue,
            f"{prefix}.tire_set.quantity",
            tire_set.quantity,
            1,
            None,
            "Die Reifenanzahl muss größer als null sein.",
        )
        _validate_range(
            add_issue,
            f"{prefix}.tire_set.width_mm",
            tire_set.width_mm,
            125,
            405,
            "Die Reifenbreite ist unplausibel.",
        )
        _validate_range(
            add_issue,
            f"{prefix}.tire_set.aspect_ratio",
            tire_set.aspect_ratio,
            20,
            95,
            "Das Reifenquerschnittsverhältnis ist unplausibel.",
        )
        _validate_range(
            add_issue,
            f"{prefix}.tire_set.rim_diameter_inch",
            tire_set.rim_diameter_inch,
            10,
            24,
            "Der Felgendurchmesser ist unplausibel.",
        )
        for tire_index, tire in enumerate(tire_set.tires):
            tire_prefix = f"{prefix}.tire_set.tires.{tire_index}"
            _validate_range(
                add_issue,
                f"{tire_prefix}.tread_depth_mm",
                tire.tread_depth_mm,
                Decimal("0"),
                Decimal("20"),
                "Die Profiltiefe ist unplausibel.",
            )
            if tire.has_damage is False and tire.damage_notes:
                add_issue(
                    f"{tire_prefix}.damage_notes",
                    "contradictory_damage",
                    "Eine Schadensnotiz setzt eine Beschädigung voraus.",
                    FieldStatus.INVALID,
                )


def _validate_tire_inspections(draft: RegistrationDraft, add_issue: IssueAdder) -> None:
    allowed_roles = {relation.role for relation in draft.tire_sets}
    for index, inspection in enumerate(draft.tire_inspections):
        prefix = f"tire_inspections.{index}"
        if inspection.tire_set_role and inspection.tire_set_role not in allowed_roles:
            add_issue(
                f"{prefix}.tire_set_role",
                "unknown_tire_set_role",
                "Die Profiltiefe verweist auf keinen erfassten Reifensatz.",
                FieldStatus.INVALID,
            )
        for name in _TREAD_FIELDS:
            _validate_range(
                add_issue,
                f"{prefix}.{name}",
                getattr(inspection, name),
                Decimal("0"),
                Decimal("20"),
                "Die Profiltiefe ist unplausibel.",
            )


def _validate_visual_inspections(
    draft: RegistrationDraft, add_issue: IssueAdder
) -> None:
    allowed_roles = {relation.role for relation in draft.tire_sets}
    for index, inspection in enumerate(draft.visual_inspections):
        prefix = f"visual_inspections.{index}"
        if inspection.tire_set_role and inspection.tire_set_role not in allowed_roles:
            add_issue(
                f"{prefix}.tire_set_role",
                "unknown_tire_set_role",
                "Die Sichtprüfung verweist auf keinen erfassten Reifensatz.",
                FieldStatus.INVALID,
            )
        if (
            inspection.result is VisualInspectionResult.NOT_OK
            and inspection.position in _NON_CONCRETE_POSITIONS
        ):
            add_issue(
                f"{prefix}.position",
                "concrete_position_required",
                "Ein n.i.O.-Befund benötigt eine konkrete Radposition.",
                FieldStatus.INVALID,
            )


def _validate_tire_change_details(
    draft: RegistrationDraft, add_issue: IssueAdder
) -> None:
    details = draft.tire_change_details
    if draft.service_type is not ServiceType.TIRE_CHANGE:
        if details is not None:
            add_issue(
                "tire_change_details",
                "wrong_protocol",
                "Wechseldetails sind nur für Reifenwechsel zulässig.",
                FieldStatus.INVALID,
            )
        return
    if details is None:
        add_issue(
            "tire_change_details",
            "required",
            "Die Wechseldetails fehlen.",
            FieldStatus.MISSING,
        )
        return
    if details.wheel_change_performed is None:
        add_issue(
            "tire_change_details.wheel_change_performed",
            "required",
            "Es fehlt, ob ein Räderwechsel durchgeführt wurde.",
            FieldStatus.MISSING,
        )
    for name in (
        "balancing_steel_count",
        "balancing_alloy_count",
        "machine_wash_count",
        "manual_wash_count",
    ):
        _validate_range(
            add_issue,
            f"tire_change_details.{name}",
            getattr(details, name),
            0,
            None,
            "Die Anzahl darf nicht negativ sein.",
        )
    for name in (
        "air_pressure_front_bar",
        "air_pressure_rear_bar",
        "wheel_bolt_torque_nm",
    ):
        _validate_range(
            add_issue,
            f"tire_change_details.{name}",
            getattr(details, name),
            Decimal("0"),
            None,
            "Der Wert darf nicht negativ sein.",
        )
    if (
        details.brake_disc_measurements
        and details.brake_visual_result is not InspectionResult.NOT_OK
    ):
        add_issue(
            "tire_change_details.brake_disc_measurements",
            "measurement_without_finding",
            "Bremsscheibenmessungen sind nur bei Bremsensichtprüfung n.i.O. zulässig.",
            FieldStatus.INVALID,
        )
    for index, measurement in enumerate(details.brake_disc_measurements):
        prefix = f"tire_change_details.brake_disc_measurements.{index}"
        if measurement.position in _NON_CONCRETE_POSITIONS:
            add_issue(
                f"{prefix}.position",
                "concrete_position_required",
                "Eine Bremsscheibenmessung benötigt eine konkrete Radposition.",
                FieldStatus.INVALID,
            )
        _validate_range(
            add_issue,
            f"{prefix}.thickness_mm",
            measurement.thickness_mm,
            Decimal("0"),
            None,
            "Die Bremsscheibendicke darf nicht negativ sein.",
        )


def _validate_range(
    add_issue: IssueAdder,
    field: str,
    value: int | Decimal | None,
    minimum: int | Decimal,
    maximum: int | Decimal | None,
    message: str,
) -> None:
    if value is None:
        return
    if value < minimum or (maximum is not None and value > maximum):
        add_issue(field, "implausible_value", message, FieldStatus.INVALID)
