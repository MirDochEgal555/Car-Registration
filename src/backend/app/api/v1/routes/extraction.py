"""Transcript-to-draft endpoint for the complete Phase-7 pipeline."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import ValidationError

from app.models.registration import ValidationResponse
from app.services.extraction import normalize_and_validate_extraction_response
from app.services.extraction_mapping import (
    ExtractionMappingError,
    map_extraction_to_registration_draft,
)
from app.services.extraction_provider import (
    ExtractionProvider,
    ExtractionProviderError,
    ExtractionProviderUnavailableError,
    get_extraction_provider,
)
from app.services.registration_validation import validate_registration


router = APIRouter(prefix="/extractions", tags=["extractions"])


@router.post(
    "",
    response_model=ValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract, normalize and validate a registration draft from a transcript",
    responses={
        422: {"description": "Transcript is missing or blank."},
        502: {"description": "The extraction provider returned unusable data."},
        503: {"description": "No extraction provider is currently available."},
    },
)
async def extract_registration_from_transcript(
    transcript: Annotated[str, Body(embed=True, min_length=1)],
    extraction_provider: Annotated[
        ExtractionProvider, Depends(get_extraction_provider)
    ],
) -> ValidationResponse:
    """Run the only supported Phase-7 hand-off from text to an internal draft.

    The transcript is passed to the provider verbatim.  Provider JSON is first
    normalised and deterministically validated against the existing strict
    extraction model, then mapped into ``RegistrationDraft`` and subjected to
    the established registration validation.  This preserves all values and
    statuses while making the endpoint directly consumable by the existing
    mechanic-review API contract.
    """

    if not transcript.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Das Transkript darf nicht leer sein.",
        )

    try:
        raw_extraction = await extraction_provider.extract(transcript)
        extraction = normalize_and_validate_extraction_response(
            raw_extraction, transcript=transcript
        )
        draft = map_extraction_to_registration_draft(transcript, extraction)
    except ExtractionProviderUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except ExtractionProviderError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
    except (ExtractionMappingError, ValidationError, ValueError) as error:
        # A strict schema violation is a provider-response failure. Returning
        # no partial draft avoids hiding an untracked value or field status.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Die KI-Extraktion hat keine verarbeitbare Antwort geliefert.",
        ) from error

    validation = validate_registration(draft)
    # Normal validation deliberately keeps browser input immutable. This new
    # pipeline endpoint owns its fresh draft, so include all final statuses in
    # the returned internal model as well as in the response envelope.
    registration = validation.registration.model_copy(deep=True)
    registration.field_status = validation.field_status
    return validation.model_copy(update={"registration": registration})
