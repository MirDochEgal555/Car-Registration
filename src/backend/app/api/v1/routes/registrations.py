"""Mechanic registration validation and delivery endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.models.registration import RegistrationDraft, SendResponse, ValidationResponse
from app.services.email import (
    EmailConfigurationError,
    EmailDeliveryError,
    EmailSender,
    get_email_sender,
)
from app.services.registration_email import render_registration_email
from app.services.registration_validation import normalize_license_plate, validate_registration


router = APIRouter(prefix="/registrations", tags=["registrations"])


@router.post(
    "/validate",
    response_model=ValidationResponse,
    summary="Validate a registration draft for mechanic review",
)
def validate_registration_draft(draft: RegistrationDraft) -> ValidationResponse:
    """Return field-level validation without persisting or modifying a draft."""

    return validate_registration(draft)


@router.post(
    "/send",
    response_model=SendResponse,
    summary="Send a confirmed registration to the office",
    responses={
        409: {"description": "Draft still has required or invalid values."},
        422: {"description": "Mechanic confirmation is missing."},
        502: {"description": "The configured mail server rejected delivery."},
        503: {"description": "Office email or SMTP is not configured."},
    },
)
def send_registration(
    draft: RegistrationDraft,
    email_sender: Annotated[EmailSender, Depends(get_email_sender)],
) -> SendResponse:
    """Deliver the current confirmed draft after one final validation pass."""

    if not draft.mechanic_confirmed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Der Vorgang muss vor dem Versand durch den Mechaniker bestätigt werden.",
        )

    validation = validate_registration(draft)
    if not validation.valid:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Der Vorgang enthält fehlende oder ungültige Pflichtangaben.",
                "validation": validation.model_dump(mode="json"),
            },
        )
    if not settings.office_email:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CARTECH_OFFICE_EMAIL ist nicht konfiguriert.",
        )

    submitted_at = datetime.now(timezone.utc)
    email = render_registration_email(validation, settings.office_email, submitted_at)
    try:
        email_sender.send(email)
    except EmailConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except EmailDeliveryError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    return SendResponse(
        registration_id=draft.id,
        submitted_at=submitted_at,
        recipient=settings.office_email,
    )
