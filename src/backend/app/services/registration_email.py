"""Rendering of complete, readable registration emails for the office."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from app.models.enums import FieldStatus, ServiceType
from app.models.registration import RegistrationDraft, ValidationResponse
from app.services.email import OutgoingEmail
from app.services.registration_validation import normalize_license_plate


_LABELS = {
    "service_type": "Protokolltyp",
    "service_date": "Protokolldatum",
    "mechanic_id": "Mechaniker",
    "license_plate": "Kennzeichen",
    "mileage_km": "Kilometerstand",
    "make": "Hersteller",
    "model": "Modell",
    "propulsion_type": "Antrieb",
    "first_registration_month": "Erstzulassung",
    "max_speed_kmh": "Höchstgeschwindigkeit",
    "vin": "FIN",
    "notes": "Notizen",
    "tire_sets": "Reifensätze",
    "tire_inspections": "Profilprüfungen",
    "visual_inspections": "Sichtprüfungen",
    "tire_change_details": "Wechseldetails",
    "customer_signature_present": "Kundenunterschrift erfasst",
    "tires": "Einzelreifen",
    "role": "Rolle",
    "tire_set": "Reifensatz",
}
_SERVICE_NAMES = {
    ServiceType.TIRE_CHANGE: "Reifenwechsel",
    ServiceType.TIRE_STORAGE: "Reifeneinlagerung",
}


def render_registration_email(
    validation: ValidationResponse,
    recipient: str,
    submitted_at: datetime,
) -> OutgoingEmail:
    """Render every supplied structured value and all review instructions."""

    registration = validation.registration
    service_name = _SERVICE_NAMES.get(registration.service_type, "Werkstattprotokoll")
    plate = registration.vehicle.license_plate or "Kennzeichen fehlt"
    if registration.vehicle.license_plate:
        plate = normalize_license_plate(registration.vehicle.license_plate)
    subject = f"CarTech {service_name} · {plate} · {registration.service_date or 'Datum fehlt'}"
    timestamp = submitted_at.astimezone().strftime("%d.%m.%Y, %H:%M %Z")

    lines = [
        f"{service_name} · abgesendet am {timestamp}",
        f"Kennzeichen: {plate}",
        f"Protokolldatum: {_display(registration.service_date)}",
        f"Mechaniker: {_display(registration.mechanic_id)}",
        "",
        "Erfasste Daten",
    ]
    data = registration.model_dump(mode="json", exclude={"id", "field_status", "raw_transcript", "mechanic_confirmed"})
    _append_data(lines, data)
    lines.extend(["", "Prüfhinweise"])
    review_entries = _review_entries(validation)
    if review_entries:
        lines.extend(f"- {entry}" for entry in review_entries)
    else:
        lines.append("- Keine Prüfhinweise.")
    return OutgoingEmail(recipient=recipient, subject=subject, body="\n".join(lines))


def _append_data(lines: list[str], data: dict[str, Any], indent: int = 0) -> None:
    for key, value in data.items():
        if value in (None, [], {}, ""):
            continue
        label = _LABELS.get(key, key.replace("_", " ").capitalize())
        prefix = "  " * indent
        if isinstance(value, dict):
            lines.append(f"{prefix}{label}:")
            _append_data(lines, value, indent + 1)
        elif isinstance(value, list):
            lines.append(f"{prefix}{label}:")
            for index, entry in enumerate(value, start=1):
                if isinstance(entry, dict):
                    lines.append(f"{prefix}  {index}.")
                    _append_data(lines, entry, indent + 2)
                else:
                    lines.append(f"{prefix}  - {_display(entry)}")
        else:
            lines.append(f"{prefix}{label}: {_display(value)}")


def _review_entries(validation: ValidationResponse) -> list[str]:
    entries = [issue.message for issue in validation.issues]
    reported_fields = {issue.field for issue in validation.issues}
    for field, status in validation.field_status.items():
        if field not in reported_fields and status is not FieldStatus.VALID:
            entries.append(f"{field}: {_display(status)}")
    return entries


def _display(value: Any) -> str:
    if isinstance(value, Enum):
        value = value.value
    if value is True:
        return "Ja"
    if value is False:
        return "Nein"
    return str(value)
