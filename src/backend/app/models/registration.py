"""Request and response models for the stateless registration workflow.

The MVP deliberately keeps drafts in the mechanic's browser session.  These
models are therefore API contracts, not database models: a client submits its
complete current draft to validation and, after confirmation, to delivery.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from pydantic import Field

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
from app.models.schemas import DomainModel, YearMonth


class VehicleDraft(DomainModel):
    """Vehicle values which may still be incomplete during mechanic review."""

    license_plate: Optional[str] = None
    mileage_km: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    propulsion_type: Optional[PropulsionType] = None
    first_registration_month: Optional[YearMonth] = None
    max_speed_kmh: Optional[int] = None
    vin: Optional[str] = None


class TireDraft(DomainModel):
    """One stored tire; all attributes remain optional while a draft is edited."""

    position: Optional[TirePosition] = None
    manufacturer: Optional[str] = None
    profile: Optional[str] = None
    tread_depth_mm: Optional[Decimal] = None
    dot: Optional[str] = None
    wear_marks_present: Optional[bool] = None
    has_damage: Optional[bool] = None
    damage_notes: Optional[str] = None


class TireSetDraft(DomainModel):
    """A tire set and, for storage records, its individual tires."""

    tire_type: Optional[TireType] = None
    width_mm: Optional[int] = None
    aspect_ratio: Optional[int] = None
    rim_diameter_inch: Optional[int] = None
    rim_category: Optional[RimCategory] = None
    rim_manufacturer: Optional[str] = None
    rim_model: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    quantity: Optional[int] = None
    dot: Optional[str] = None
    load_index: Optional[str] = None
    speed_index: Optional[str] = None
    notes: Optional[str] = None
    tires: list[TireDraft] = Field(default_factory=list)


class RegistrationTireSet(DomainModel):
    """A tire set with an explicit service-specific role."""

    role: TireSetRole
    tire_set: TireSetDraft


class TireInspectionDraft(DomainModel):
    """Tread-depth readings tied to a tire-set role."""

    tire_set_role: Optional[TireSetRole] = None
    tread_front_left_mm: Optional[Decimal] = None
    tread_front_right_mm: Optional[Decimal] = None
    tread_rear_left_mm: Optional[Decimal] = None
    tread_rear_right_mm: Optional[Decimal] = None
    tread_front_mm: Optional[Decimal] = None
    tread_rear_mm: Optional[Decimal] = None
    notes: Optional[str] = None


class TireConditionDraft(DomainModel):
    """A spoken tire finding, kept separate so multiple findings are lossless."""

    tire_set_role: Optional[TireSetRole] = None
    condition: Optional[TireConditionType] = None
    position: Optional[TirePosition] = None
    notes: Optional[str] = None


class VisualInspectionDraft(DomainModel):
    """A visual wheel or tire inspection from a tire-change record."""

    tire_set_role: Optional[TireSetRole] = None
    component: Optional[VisualInspectionComponent] = None
    result: Optional[VisualInspectionResult] = None
    position: Optional[TirePosition] = None
    notes: Optional[str] = None


class BrakeDiscMeasurementDraft(DomainModel):
    """A brake-disc thickness measurement associated with a tire change."""

    position: Optional[TirePosition] = None
    thickness_mm: Optional[Decimal] = None


class TireChangeDetailsDraft(DomainModel):
    """Values unique to a tire-change protocol, editable while incomplete."""

    wheel_change_performed: Optional[bool] = None
    balancing_steel_count: Optional[int] = None
    balancing_alloy_count: Optional[int] = None
    machine_wash_count: Optional[int] = None
    manual_wash_count: Optional[int] = None
    whm_mode: Optional[str] = None
    next_customer_service: Optional[str] = None
    next_oil_service: Optional[str] = None
    air_pressure_front_bar: Optional[Decimal] = None
    air_pressure_rear_bar: Optional[Decimal] = None
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
    wheel_bolt_torque_nm: Optional[Decimal] = None
    whatsapp_contact_allowed: Optional[bool] = None
    brake_disc_measurements: list[BrakeDiscMeasurementDraft] = Field(default_factory=list)


class RegistrationDraft(DomainModel):
    """The complete client-owned registration draft.

    `mechanic_confirmed` is intentionally client supplied.  The API does not
    persist an approval in the MVP, so a send request must state the explicit
    confirmation that immediately preceded it.
    """

    id: UUID = Field(default_factory=uuid4)
    service_type: Optional[ServiceType] = None
    service_date: Optional[date] = None
    mechanic_id: Optional[UUID] = None
    mechanic_confirmed: bool = False
    vehicle: VehicleDraft = Field(default_factory=VehicleDraft)
    notes: Optional[str] = None
    raw_transcript: Optional[str] = None
    field_status: dict[str, FieldStatus] = Field(default_factory=dict)
    tire_sets: list[RegistrationTireSet] = Field(default_factory=list)
    tire_inspections: list[TireInspectionDraft] = Field(default_factory=list)
    conditions: list[TireConditionDraft] = Field(default_factory=list)
    visual_inspections: list[VisualInspectionDraft] = Field(default_factory=list)
    tire_change_details: Optional[TireChangeDetailsDraft] = None
    customer_signature_present: bool = False


class ValidationIssue(DomainModel):
    """A machine-readable field error or review warning."""

    field: str
    code: str
    message: str
    status: FieldStatus


class ValidationResponse(DomainModel):
    """Validation result returned without modifying or persisting a draft."""

    registration: RegistrationDraft
    valid: bool
    review_required: bool
    field_status: dict[str, FieldStatus]
    issues: list[ValidationIssue]
    status: ServiceStatus = ServiceStatus.MECHANIC_REVIEW


class DeliveryStatusResponse(DomainModel):
    """Durable delivery state for a confirmed registration."""

    registration_id: UUID
    status: ServiceStatus
    recipient: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None
    attempt_count: int = Field(ge=0)
    last_error: Optional[str] = None


class SendResponse(DeliveryStatusResponse):
    """Result of a successfully accepted email delivery."""

    status: ServiceStatus = ServiceStatus.EMAIL_SENT
    submitted_at: datetime
    recipient: str


__all__ = [
    "RegistrationDraft",
    "DeliveryStatusResponse",
    "SendResponse",
    "TireConditionDraft",
    "ValidationIssue",
    "ValidationResponse",
]
