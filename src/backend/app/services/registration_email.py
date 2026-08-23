"""Render registration emails as matching HTML and plain-text alternatives.

The semantic document in this module is intentionally built once from the
validated registration.  Both mail formats consume that document, which keeps
the information and review notes identical for graphical and text-only mail
clients.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from html import escape
from typing import Any

from app.models.enums import FieldStatus, ServiceType
from app.models.registration import ValidationResponse
from app.services.email import OutgoingEmail
from app.services.registration_validation import normalize_license_plate


_LABELS = {
    "service_type": "Protokolltyp",
    "service_date": "Protokolldatum",
    "mechanic_id": "Mechaniker",
    "vehicle": "Fahrzeug",
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
    "tire_type": "Reifenart",
    "width_mm": "Reifenbreite",
    "aspect_ratio": "Reifenquerschnitt",
    "rim_diameter_inch": "Felgendurchmesser",
    "rim_category": "Felgenart",
    "rim_manufacturer": "Felgenhersteller",
    "rim_model": "Felgenmodell",
    "manufacturer": "Hersteller",
    "quantity": "Anzahl",
    "dot": "DOT",
    "load_index": "Lastindex",
    "speed_index": "Geschwindigkeitsindex",
    "position": "Position",
    "profile": "Profil",
    "tread_depth_mm": "Profiltiefe",
    "wear_marks_present": "Verschleißmarkierungen vorhanden",
    "has_damage": "Beschädigung vorhanden",
    "damage_notes": "Schadensnotiz",
    "tire_set_role": "Reifensatzrolle",
    "tread_front_left_mm": "Profiltiefe vorne links",
    "tread_front_right_mm": "Profiltiefe vorne rechts",
    "tread_rear_left_mm": "Profiltiefe hinten links",
    "tread_rear_right_mm": "Profiltiefe hinten rechts",
    "tread_front_mm": "Profiltiefe vorne",
    "tread_rear_mm": "Profiltiefe hinten",
    "component": "Bauteil",
    "result": "Ergebnis",
    "wheel_change_performed": "Räder gewechselt",
    "balancing_steel_count": "Gewuchtete Stahlräder",
    "balancing_alloy_count": "Gewuchtete Aluräder",
    "machine_wash_count": "Maschinell gewaschene Räder",
    "manual_wash_count": "Manuell gewaschene Räder",
    "whm_mode": "WHM-Modus",
    "next_customer_service": "Nächster Kundendienst",
    "next_oil_service": "Nächster Ölservice",
    "air_pressure_front_bar": "Luftdruck vorne",
    "air_pressure_rear_bar": "Luftdruck hinten",
    "wheel_lock_present": "Felgenschloss vorhanden",
    "wheel_bolt_configuration": "Radschraubenkonfiguration",
    "hu_due_month": "HU fällig",
    "suspension_visual_result": "Sichtprüfung Fahrwerk",
    "brake_visual_result": "Sichtprüfung Bremsen",
    "hub_cleaned": "Radnabe gereinigt",
    "rdks_type": "RDKS-Typ",
    "rdks_programmed": "RDKS programmiert",
    "speed_limiter_set": "Geschwindigkeitsbegrenzer gesetzt",
    "speed_limiter_sticker_applied": "Aufkleber Geschwindigkeitsbegrenzer angebracht",
    "wheel_bolt_torque_nm": "Anzugsdrehmoment Radschrauben",
    "whatsapp_contact_allowed": "WhatsApp-Kontakt erlaubt",
    "brake_disc_measurements": "Bremsscheibenmessungen",
    "thickness_mm": "Dicke",
}
_SERVICE_NAMES = {
    ServiceType.TIRE_CHANGE: "Reifenwechsel",
    ServiceType.TIRE_STORAGE: "Reifeneinlagerung",
}
_SINGULAR_LABELS = {
    "tire_sets": "Reifensatz",
    "tires": "Einzelreifen",
    "tire_inspections": "Profilprüfung",
    "visual_inspections": "Sichtprüfung",
    "brake_disc_measurements": "Bremsscheibenmessung",
}
_VALUE_LABELS = {
    "electric": "Elektro",
    "hybrid": "Hybrid",
    "other": "Sonstiger",
    "unknown": "Unbekannt",
    "tire_change": "Reifenwechsel",
    "tire_storage": "Reifeneinlagerung",
    "summer": "Sommerreifen",
    "winter": "Winterreifen",
    "all_season": "Ganzjahresreifen",
    "alloy": "Aluminium",
    "steel": "Stahl",
    "original": "Original",
    "installed": "Montiert",
    "removed": "Demontiert",
    "stored": "Eingelagert",
    "front_left": "Vorne links",
    "front_right": "Vorne rechts",
    "rear_left": "Hinten links",
    "rear_right": "Hinten rechts",
    "front": "Vorne",
    "rear": "Hinten",
    "all": "Alle",
    "ok": "In Ordnung",
    "not_ok": "Nicht in Ordnung",
    "active": "Aktiv",
    "passive": "Passiv",
    "same": "Gleich",
    "different": "Unterschiedlich",
    "rim": "Felge",
    "tire": "Reifen",
    "missing": "Fehlt",
    "uncertain": "Unsicher",
    "invalid": "Unplausibel",
    "valid": "Gültig",
}
_UNITS = {
    "mileage_km": " km",
    "max_speed_kmh": " km/h",
    "width_mm": " mm",
    "rim_diameter_inch": " Zoll",
    "tread_depth_mm": " mm",
    "tread_front_left_mm": " mm",
    "tread_front_right_mm": " mm",
    "tread_rear_left_mm": " mm",
    "tread_rear_right_mm": " mm",
    "tread_front_mm": " mm",
    "tread_rear_mm": " mm",
    "air_pressure_front_bar": " bar",
    "air_pressure_rear_bar": " bar",
    "wheel_bolt_torque_nm": " Nm",
    "thickness_mm": " mm",
}


@dataclass(frozen=True)
class EmailField:
    """One label/value pair or a labelled collection of nested fields."""

    label: str
    value: str | None = None
    children: tuple["EmailField", ...] = ()


@dataclass(frozen=True)
class RegistrationEmailDocument:
    """Presentation model shared by the text and HTML email renderers."""

    service_name: str
    license_plate: str
    submitted_at: str
    fields: tuple[EmailField, ...]
    review_entries: tuple[str, ...]


def render_registration_email(
    validation: ValidationResponse,
    recipient: str,
    submitted_at: datetime,
) -> OutgoingEmail:
    """Render a complete multipart-ready office email from one document."""

    registration = validation.registration
    service_name = _SERVICE_NAMES.get(registration.service_type, "Werkstattprotokoll")
    plate = registration.vehicle.license_plate or "Kennzeichen fehlt"
    if registration.vehicle.license_plate:
        plate = normalize_license_plate(registration.vehicle.license_plate)
    subject = f"CarTech {service_name} · {plate} · {registration.service_date or 'Datum fehlt'}"
    timestamp = submitted_at.astimezone().strftime("%d.%m.%Y, %H:%M %Z")
    document = build_registration_email_document(
        validation,
        service_name=service_name,
        license_plate=plate,
        submitted_at=timestamp,
    )
    return OutgoingEmail(
        recipient=recipient,
        subject=subject,
        body=render_registration_email_text(document),
        html_body=render_registration_email_html(document),
    )


def build_registration_email_document(
    validation: ValidationResponse,
    *,
    service_name: str,
    license_plate: str,
    submitted_at: str,
) -> RegistrationEmailDocument:
    """Create the one semantic mail document used for both alternatives."""

    data = validation.registration.model_dump(
        mode="python",
        exclude={"id", "field_status", "raw_transcript", "mechanic_confirmed"},
    )
    fields = tuple(
        field
        for key, value in data.items()
        if (field := _to_email_field(key, value)) is not None
    )
    return RegistrationEmailDocument(
        service_name=service_name,
        license_plate=license_plate,
        submitted_at=submitted_at,
        fields=fields,
        review_entries=tuple(_review_entries(validation)),
    )


def render_registration_email_text(document: RegistrationEmailDocument) -> str:
    """Render the shared document for text-only mail clients."""

    lines = [
        "CarTech Werkstattprotokoll",
        f"{document.service_name} · abgesendet am {document.submitted_at}",
        f"Kennzeichen: {document.license_plate}",
        "",
        "Erfasste Daten",
    ]
    for field in document.fields:
        _append_text_field(lines, field)
    lines.extend(["", "Prüfhinweise"])
    if document.review_entries:
        lines.extend(f"- {entry}" for entry in document.review_entries)
    else:
        lines.append("- Keine Prüfhinweise.")
    return "\n".join(lines)


def render_registration_email_html(document: RegistrationEmailDocument) -> str:
    """Render the shared document as a conservative, email-client-safe HTML mail."""

    field_rows = "".join(_render_html_field(field) for field in document.fields)
    review_rows = (
        "".join(f"<li>{escape(entry)}</li>" for entry in document.review_entries)
        if document.review_entries
        else "<li>Keine Prüfhinweise.</li>"
    )
    review_style = "#9a3412" if document.review_entries else "#166534"
    return f"""<!doctype html>
<html lang="de">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(document.service_name)}</title>
  </head>
  <body style="margin:0;padding:0;background:#f4f7fb;color:#172033;font-family:Arial,Helvetica,sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#f4f7fb;">
      <tr><td align="center" style="padding:24px 12px;">
        <table role="presentation" width="680" cellspacing="0" cellpadding="0" border="0" style="width:100%;max-width:680px;background:#ffffff;border:1px solid #dbe3ef;border-radius:12px;overflow:hidden;">
          <tr><td style="padding:24px 28px;background:#123b64;color:#ffffff;">
            <div style="font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;">CarTech</div>
            <div style="margin-top:8px;font-size:25px;font-weight:700;line-height:1.25;">{escape(document.service_name)}</div>
            <div style="margin-top:6px;font-size:16px;line-height:1.4;">Kennzeichen: <strong>{escape(document.license_plate)}</strong></div>
          </td></tr>
          <tr><td style="padding:20px 28px 8px;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#edf5ff;border:1px solid #c9dff5;border-radius:8px;">
              <tr><td style="padding:12px 14px;font-size:14px;line-height:1.45;"><strong>Abgesendet:</strong> {escape(document.submitted_at)}</td></tr>
            </table>
          </td></tr>
          <tr><td style="padding:20px 28px 8px;font-size:19px;font-weight:700;">Erfasste Daten</td></tr>
          <tr><td style="padding:0 28px 20px;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="border:1px solid #dbe3ef;border-radius:8px;overflow:hidden;">{field_rows}</table>
          </td></tr>
          <tr><td style="padding:4px 28px 8px;font-size:19px;font-weight:700;">Prüfhinweise</td></tr>
          <tr><td style="padding:0 28px 28px;">
            <div style="padding:12px 16px;border:1px solid #fed7aa;border-radius:8px;background:#fff7ed;color:{review_style};font-size:14px;line-height:1.5;">
              <ul style="margin:0;padding-left:20px;">{review_rows}</ul>
            </div>
          </td></tr>
        </table>
      </td></tr>
    </table>
  </body>
</html>"""


def _to_email_field(key: str, value: Any, *, label: str | None = None) -> EmailField | None:
    """Turn one serialized domain value into a labelled presentation field."""

    if value in (None, [], {}, ""):
        return None
    field_label = label or _LABELS.get(key, key.replace("_", " ").capitalize())
    if isinstance(value, dict):
        children = tuple(
            child
            for child_key, child_value in value.items()
            if (child := _to_email_field(child_key, child_value)) is not None
        )
        return EmailField(field_label, children=children) if children else None
    if isinstance(value, list):
        singular_label = _SINGULAR_LABELS.get(key, "Eintrag")
        children = tuple(
            child
            for index, entry in enumerate(value, start=1)
            if (
                child := _to_email_field(
                    key,
                    entry,
                    label=f"{singular_label} {index}",
                )
            )
            is not None
        )
        return EmailField(field_label, children=children) if children else None
    return EmailField(field_label, value=_display(value, key=key))


def _append_text_field(
    lines: list[str], field: EmailField, indent: int = 0
) -> None:
    prefix = "  " * indent
    if field.children:
        lines.append(f"{prefix}{field.label}:")
        for child in field.children:
            _append_text_field(lines, child, indent + 1)
    elif field.value is not None:
        lines.append(f"{prefix}{field.label}: {field.value}")


def _render_html_field(field: EmailField, depth: int = 0) -> str:
    """Render field nesting as table rows; only escaped document strings enter HTML."""

    padding = 14 + depth * 16
    if field.children:
        heading = (
            "<tr><td colspan=\"2\" style=\"padding:10px 14px 6px;"
            f"padding-left:{padding}px;background:#f8fafc;color:#123b64;font-size:14px;"
            f"font-weight:700;border-top:1px solid #dbe3ef;\">{escape(field.label)}</td></tr>"
        )
        return heading + "".join(
            _render_html_field(child, depth + 1) for child in field.children
        )
    if field.value is None:
        return ""
    return (
        "<tr>"
        f"<td style=\"width:43%;padding:9px 12px 9px {padding}px;vertical-align:top;"
        "color:#526176;font-size:14px;line-height:1.4;border-top:1px solid #e6edf5;\">"
        f"{escape(field.label)}</td>"
        "<td style=\"padding:9px 14px;vertical-align:top;color:#172033;font-size:14px;"
        f"line-height:1.4;border-top:1px solid #e6edf5;\">{escape(field.value)}</td>"
        "</tr>"
    )


def _review_entries(validation: ValidationResponse) -> list[str]:
    entries = [issue.message for issue in validation.issues]
    reported_fields = {issue.field for issue in validation.issues}
    for field, status in validation.field_status.items():
        if field not in reported_fields and status is not FieldStatus.VALID:
            entries.append(f"{_display_field_path(field)}: {_display(status)}")
    return entries


def _display_field_path(path: str) -> str:
    """Make a field-status path suitable for an office user, not an API user."""

    parts: list[str] = []
    for part in path.split("."):
        if part.isdigit() and parts:
            parts[-1] = f"{parts[-1]} {int(part) + 1}"
        else:
            parts.append(_LABELS.get(part, part.replace("_", " ").capitalize()))
    return " · ".join(parts)


def _display(value: Any, *, key: str | None = None) -> str:
    if isinstance(value, Enum):
        rendered = _VALUE_LABELS.get(value.value, value.value)
        return f"{rendered}{_UNITS.get(key, '')}"
    if value is True:
        return "Ja"
    if value is False:
        return "Nein"
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y")
    return f"{value}{_UNITS.get(key, '')}"
