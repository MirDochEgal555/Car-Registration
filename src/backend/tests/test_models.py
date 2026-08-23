from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models import (
    FieldStatus,
    ServiceRecord,
    ServiceType,
    Tire,
    TirePosition,
    Vehicle,
    VisualInspection,
    VisualInspectionComponent,
    VisualInspectionResult,
)


def test_vehicle_serializes_a_year_month_without_a_day() -> None:
    vehicle = Vehicle(license_plate="CW-AB 123", first_registration_month="2024-03")

    assert vehicle.model_dump(mode="json")["first_registration_month"] == "2024-03"


def test_vehicle_rejects_an_invalid_year_month() -> None:
    with pytest.raises(ValidationError):
        Vehicle(license_plate="CW-AB 123", first_registration_month="2024-13")


def test_service_record_derives_review_requirement_from_field_status() -> None:
    record = ServiceRecord(
        vehicle_id=uuid4(),
        created_by=uuid4(),
        service_type=ServiceType.TIRE_CHANGE,
        service_date=date(2026, 8, 23),
        field_status={"model": FieldStatus.UNCERTAIN},
        review_required=False,
    )

    assert record.field_status == {"model": FieldStatus.UNCERTAIN}
    assert record.review_required is True


@pytest.mark.parametrize(
    ("field_status", "review_required"),
    [
        (None, False),
        ({"model": FieldStatus.VALID}, False),
        ({"model": FieldStatus.MISSING}, False),
        ({"model": FieldStatus.UNCERTAIN}, True),
        ({"mileage_km": FieldStatus.INVALID}, True),
        (
            {
                "model": FieldStatus.VALID,
                "vin": FieldStatus.MISSING,
                "mileage_km": FieldStatus.INVALID,
            },
            True,
        ),
    ],
)
def test_service_record_calculates_review_requirement_for_all_field_statuses(
    field_status: dict[str, FieldStatus] | None, review_required: bool
) -> None:
    record = ServiceRecord(
        vehicle_id=uuid4(),
        created_by=uuid4(),
        service_type=ServiceType.TIRE_CHANGE,
        service_date=date(2026, 8, 23),
        field_status=field_status,
        review_required=not review_required,
    )

    assert record.review_required is review_required


def test_service_record_recalculates_review_requirement_when_statuses_change() -> None:
    record = ServiceRecord(
        vehicle_id=uuid4(),
        created_by=uuid4(),
        service_type=ServiceType.TIRE_CHANGE,
        service_date=date(2026, 8, 23),
        field_status={"model": FieldStatus.VALID},
    )

    record.field_status = {"model": FieldStatus.UNCERTAIN}

    assert record.review_required is True


def test_stored_tire_allows_documented_damage_without_inventing_notes() -> None:
    tire = Tire(
        tire_set_id=uuid4(),
        position=TirePosition.FRONT_LEFT,
        wear_marks_present=False,
        has_damage=True,
    )

    assert tire.damage_notes is None


def test_non_ok_visual_inspection_requires_a_concrete_position() -> None:
    with pytest.raises(ValidationError, match="concrete wheel position"):
        VisualInspection(
            service_record_id=uuid4(),
            service_tire_set_id=uuid4(),
            component=VisualInspectionComponent.RIM,
            result=VisualInspectionResult.NOT_OK,
            position=TirePosition.ALL,
        )
