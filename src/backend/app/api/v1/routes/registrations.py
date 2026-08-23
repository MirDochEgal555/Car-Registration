"""Mechanic registration validation and delivery endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.models.enums import ServiceStatus
from app.models.registration import (
    DeliveryStatusResponse,
    RegistrationDraft,
    SendResponse,
    ValidationResponse,
)
from app.services.delivery_store import (
    DeliveryAlreadySentError,
    DeliveryConflictError,
    DeliveryInProgressError,
    DeliveryRecipientMissingError,
    DeliveryStore,
    DeliveryStoreError,
    StoredDelivery,
)
from app.services.email import (
    EmailConfigurationError,
    EmailDeliveryError,
    EmailSender,
    get_email_sender,
)
from app.services.registration_email import render_registration_email
from app.services.registration_validation import normalize_license_plate, validate_registration


router = APIRouter(prefix="/registrations", tags=["registrations"])


def get_delivery_store() -> DeliveryStore:
    """Return the configured durable outbox for one request."""

    return DeliveryStore(settings.delivery_store_path)


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
        502: {
            "description": "Delivery failed; the registration is safely saved for retry."
        },
        503: {
            "description": "Delivery cannot start; the registration is safely saved for retry."
        },
    },
)
def send_registration(
    draft: RegistrationDraft,
    email_sender: Annotated[EmailSender, Depends(get_email_sender)],
    delivery_store: Annotated[DeliveryStore, Depends(get_delivery_store)],
) -> SendResponse:
    """Save a confirmed draft first, then attempt an idempotent email delivery."""

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
    try:
        delivery, _ = delivery_store.save_or_get(
            validation.registration,
            settings.office_email,
        )
    except DeliveryConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except DeliveryStoreError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    if delivery.status is ServiceStatus.EMAIL_SENT:
        return _send_response(delivery)

    return _attempt_delivery(delivery, email_sender, delivery_store)


@router.get(
    "/{registration_id}/delivery-status",
    response_model=DeliveryStatusResponse,
    summary="Read the durable email delivery status",
)
def get_delivery_status(
    registration_id: UUID,
    delivery_store: Annotated[DeliveryStore, Depends(get_delivery_store)],
) -> DeliveryStatusResponse:
    """Expose failures and retryability without returning stored vehicle data."""

    try:
        delivery = delivery_store.get(registration_id)
    except DeliveryStoreError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    if delivery is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Für diese Vorgangs-ID wurde kein Versandauftrag gefunden.",
        )
    return _delivery_status_response(delivery)


@router.post(
    "/{registration_id}/retry",
    response_model=SendResponse,
    summary="Retry a saved failed registration delivery",
    responses={
        409: {"description": "Delivery is already successful or in progress."},
        502: {"description": "Delivery failed again; the registration remains saved."},
        503: {"description": "Delivery cannot start; the registration remains saved."},
    },
)
def retry_registration_delivery(
    registration_id: UUID,
    email_sender: Annotated[EmailSender, Depends(get_email_sender)],
    delivery_store: Annotated[DeliveryStore, Depends(get_delivery_store)],
) -> SendResponse:
    """Retry the immutable, previously saved registration without a request body."""

    try:
        delivery = delivery_store.get(registration_id)
    except DeliveryStoreError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    if delivery is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Für diese Vorgangs-ID wurde kein Versandauftrag gefunden.",
        )
    if delivery.status is ServiceStatus.EMAIL_SENT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Der Vorgang wurde bereits erfolgreich versendet.",
        )

    return _attempt_delivery(delivery, email_sender, delivery_store)


def _attempt_delivery(
    delivery: StoredDelivery,
    email_sender: EmailSender,
    delivery_store: DeliveryStore,
) -> SendResponse:
    """Claim, render and deliver a saved record while preserving every outcome."""

    try:
        claimed_delivery = delivery_store.start_attempt(
            delivery.registration_id,
            settings.office_email,
        )
    except DeliveryAlreadySentError:
        try:
            already_sent = delivery_store.get(delivery.registration_id)
        except DeliveryStoreError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(error),
            ) from error
        if already_sent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Für diese Vorgangs-ID wurde kein Versandauftrag gefunden.",
            )
        return _send_response(already_sent)
    except DeliveryInProgressError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except DeliveryRecipientMissingError as error:
        return _raise_saved_delivery_failure(
            delivery,
            delivery_store,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_message=str(error),
        )
    except DeliveryStoreError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    try:
        assert claimed_delivery.recipient is not None
        validation = validate_registration(claimed_delivery.registration)
        submitted_at = claimed_delivery.last_attempt_at or datetime.now(timezone.utc)
        email = render_registration_email(
            validation,
            claimed_delivery.recipient,
            submitted_at,
        )
        email_sender.send(email)
    except EmailConfigurationError as error:
        return _raise_saved_delivery_failure(
            claimed_delivery,
            delivery_store,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_message=str(error),
        )
    except EmailDeliveryError as error:
        return _raise_saved_delivery_failure(
            claimed_delivery,
            delivery_store,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_message=str(error),
        )
    except Exception:
        # Never leave a record in an opaque "sending" state if rendering or an
        # adapter implementation unexpectedly fails.
        return _raise_saved_delivery_failure(
            claimed_delivery,
            delivery_store,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_message=(
                "Beim Versand ist ein unerwarteter Fehler aufgetreten. "
                "Der Vorgang wurde gespeichert und kann erneut versendet werden."
            ),
        )

    try:
        delivered = delivery_store.mark_sent(
            claimed_delivery.registration_id,
            submitted_at,
        )
    except DeliveryStoreError as error:
        # SMTP may already have accepted the mail; reporting a success here
        # would hide the missing audit state.  The persistent pre-send record
        # remains recoverable as email_sending on restart.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Die E-Mail wurde übergeben, aber der Versandstatus konnte nicht "
                "dauerhaft gespeichert werden. Bitte den Versandstatus prüfen."
            ),
        ) from error
    return _send_response(delivered)


def _raise_saved_delivery_failure(
    delivery: StoredDelivery,
    delivery_store: DeliveryStore,
    *,
    status_code: int,
    error_message: str,
) -> SendResponse:
    """Store an error before returning a retry instruction to the client."""

    try:
        failed = delivery_store.mark_failed(delivery.registration_id, error_message)
    except DeliveryStoreError as storage_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Der Versand ist fehlgeschlagen und der Fehlerstatus konnte nicht "
                "dauerhaft gespeichert werden."
            ),
        ) from storage_error

    raise HTTPException(
        status_code=status_code,
        detail={
            "message": (
                "Der Versand ist fehlgeschlagen. Der Vorgang wurde gespeichert "
                "und kann erneut versendet werden."
            ),
            "delivery": _delivery_status_response(failed).model_dump(mode="json"),
            "retry_endpoint": f"/api/v1/registrations/{failed.registration_id}/retry",
        },
    )


def _send_response(delivery: StoredDelivery) -> SendResponse:
    """Convert a successful durable record to the public send response."""

    assert delivery.status is ServiceStatus.EMAIL_SENT
    assert delivery.recipient is not None
    assert delivery.submitted_at is not None
    return SendResponse(**_delivery_status_response(delivery).model_dump())


def _delivery_status_response(delivery: StoredDelivery) -> DeliveryStatusResponse:
    """Expose delivery metadata but deliberately not the saved registration body."""

    return DeliveryStatusResponse(
        registration_id=delivery.registration_id,
        status=delivery.status,
        recipient=delivery.recipient,
        created_at=delivery.created_at,
        updated_at=delivery.updated_at,
        submitted_at=delivery.submitted_at,
        last_attempt_at=delivery.last_attempt_at,
        attempt_count=delivery.attempt_count,
        last_error=delivery.last_error,
    )
