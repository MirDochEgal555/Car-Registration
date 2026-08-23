"""Pydantic representations of the optional CarTech target data model.

These models do not introduce a database. They provide one typed contract for
the future extraction, validation, email, and persistence layers while WERBAS
continues to be the MVP's source of truth.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Annotated, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import (
    FieldStatus,
    InspectionResult,
    PropulsionType,
    RdksType,
    RimCategory,
    ServiceStatus,
    ServiceType,
    TireConditionType,
    TirePosition,
    TireSetRole,
    TireType,
    VisualInspectionComponent,
    VisualInspectionResult,
    WheelBoltConfiguration,
)

YearMonth = Annotated[
    str,
    Field(
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        description="Month and year in YYYY-MM form, without an invented day.",
        examples=["2024-03"],
    ),
]

NonNegativeDecimal = Annotated[Decimal, Field(ge=0)]


def utc_now() -> datetime:
    """Provide timezone-aware timestamps for newly created model instances."""

    return datetime.now(timezone.utc)


class DomainModel(BaseModel):
    """Shared serialization and input policy for CarTech domain data."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class IdentifiedModel(DomainModel):
    id: UUID = Field(default_factory=uuid4, description="Internal identifier.")


class TimestampedModel(IdentifiedModel):
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Customer(TimestampedModel):
    """Customer master data; WERBAS assignment remains an office task."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None
    werbas_customer_id: Optional[str] = None


class Vehicle(TimestampedModel):
    """Vehicle master data that may exist before office customer matching."""

    customer_id: Optional[UUID] = None
    license_plate: str = Field(min_length=1)
    mileage_km: Optional[int] = Field(default=None, ge=0)
    make: Optional[str] = None
    model: Optional[str] = None
    propulsion_type: Optional[PropulsionType] = None
    first_registration_month: Optional[YearMonth] = None
    max_speed_kmh: Optional[int] = Field(default=None, gt=0)
    vin: Optional[str] = None
    werbas_vehicle_id: Optional[str] = None


class ServiceRecord(TimestampedModel):
    """A tire-change or tire-storage service record."""

    vehicle_id: UUID
    service_type: ServiceType
    service_date: date
    status: ServiceStatus = ServiceStatus.DRAFT
    notes: Optional[str] = None
    raw_transcript: Optional[str] = None
    extraction_payload: Optional[dict[str, Any]] = None
    field_status: Optional[dict[str, FieldStatus]] = None
    review_required: bool = False
    created_by: UUID
    mechanic_confirmed_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    office_reviewed_at: Optional[datetime] = None
    werbas_order_id: Optional[str] = None


class CustomerSignature(IdentifiedModel):
    """Protected binary customer signature, never part of a speech transcript."""

    service_record_id: UUID
    customer_signature: bytes
    customer_signed_at: datetime


class TireChangeDetails(IdentifiedModel):
    """The single tire-change-specific extension for a service record."""

    service_record_id: UUID
    wheel_change_performed: bool
    balancing_steel_count: Optional[int] = Field(default=None, ge=0)
    balancing_alloy_count: Optional[int] = Field(default=None, ge=0)
    machine_wash_count: Optional[int] = Field(default=None, ge=0)
    manual_wash_count: Optional[int] = Field(default=None, ge=0)
    whm_mode: Optional[str] = None
    next_customer_service: Optional[str] = None
    next_oil_service: Optional[str] = None
    air_pressure_front_bar: Optional[NonNegativeDecimal] = None
    air_pressure_rear_bar: Optional[NonNegativeDecimal] = None
    wheel_lock_present: Optional[bool] = None
    wheel_bolt_configuration: Optional[WheelBoltConfiguration] = None
    hu_due_month: Optional[YearMonth] = None
    suspension_visual_result: Optional[InspectionResult] = None
    brake_visual_result: Optional[InspectionResult] = None
    hub_cleaned: Optional[bool] = None
    rdks_type: Optional[RdksType] = None
    rdks_programmed: Optional[bool] = None
    speed_limiter_set: Optional[bool] = None
    speed_limiter_sticker_applied: Optional[bool] = None
    wheel_bolt_torque_nm: Optional[NonNegativeDecimal] = None
    whatsapp_contact_allowed: Optional[bool] = None


class BrakeDiscMeasurement(IdentifiedModel):
    """A brake-disc measurement recorded after a non-OK brake inspection."""

    tire_change_details_id: UUID
    position: TirePosition
    thickness_mm: NonNegativeDecimal


class TireSet(IdentifiedModel):
    """Shared attributes of a set of tires and its rim."""

    tire_type: Optional[TireType] = None
    width_mm: Optional[int] = Field(default=None, gt=0)
    aspect_ratio: Optional[int] = Field(default=None, gt=0)
    rim_diameter_inch: Optional[int] = Field(default=None, gt=0)
    rim_category: Optional[RimCategory] = None
    rim_manufacturer: Optional[str] = None
    rim_model: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    quantity: Optional[int] = Field(default=None, gt=0)
    dot: Optional[str] = None
    load_index: Optional[str] = None
    speed_index: Optional[str] = None
    notes: Optional[str] = None


class Tire(IdentifiedModel):
    """Per-wheel details used for tire-storage records."""

    tire_set_id: UUID
    position: TirePosition
    manufacturer: Optional[str] = None
    profile: Optional[str] = None
    tread_depth_mm: Optional[NonNegativeDecimal] = None
    dot: Optional[str] = None
    wear_marks_present: bool
    has_damage: bool
    damage_notes: Optional[str] = None


class ServiceTireSet(IdentifiedModel):
    """Relates a tire set to a service record and preserves its role."""

    service_record_id: UUID
    tire_set_id: UUID
    role: TireSetRole


class TireInspection(IdentifiedModel):
    """Tread-depth readings and notes for a tire-change service."""

    service_record_id: UUID
    service_tire_set_id: Optional[UUID] = None
    tread_front_left_mm: Optional[NonNegativeDecimal] = None
    tread_front_right_mm: Optional[NonNegativeDecimal] = None
    tread_rear_left_mm: Optional[NonNegativeDecimal] = None
    tread_rear_right_mm: Optional[NonNegativeDecimal] = None
    tread_front_mm: Optional[NonNegativeDecimal] = None
    tread_rear_mm: Optional[NonNegativeDecimal] = None
    notes: Optional[str] = None


class VisualInspection(IdentifiedModel):
    """Rim or tire visual inspection for a tire-change tire set."""

    service_record_id: UUID
    service_tire_set_id: UUID
    component: VisualInspectionComponent
    result: VisualInspectionResult
    position: TirePosition
    notes: Optional[str] = None

    @model_validator(mode="after")
    def non_ok_result_needs_concrete_position(self) -> "VisualInspection":
        if self.result is VisualInspectionResult.NOT_OK and self.position in {
            TirePosition.ALL,
            TirePosition.UNKNOWN,
            TirePosition.FRONT,
            TirePosition.REAR,
        }:
            raise ValueError(
                "a not_ok visual inspection requires a concrete wheel position"
            )
        return self


class TireCondition(IdentifiedModel):
    """An individual tire condition so several findings remain lossless."""

    tire_inspection_id: UUID
    condition: TireConditionType
    position: TirePosition
    notes: Optional[str] = None


__all__ = [
    "BrakeDiscMeasurement",
    "Customer",
    "CustomerSignature",
    "DomainModel",
    "ServiceRecord",
    "ServiceTireSet",
    "Tire",
    "TireChangeDetails",
    "TireCondition",
    "TireInspection",
    "TireSet",
    "Vehicle",
    "VisualInspection",
    "YearMonth",
]
