"""Workshop-audio upload and transcription endpoints."""

from __future__ import annotations

from typing import Annotated, Optional, Union

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.services.transcription import (
    AudioRecording,
    TranscriptionProvider,
    TranscriptionProviderError,
    TranscriptionProviderUnavailableError,
    get_transcription_provider,
)


router = APIRouter(prefix="/audio", tags=["audio"])

# The current browser recorder explicitly creates a Blob with this MIME type.
# Parameters such as ``;codecs=opus`` are normalised before this allow-list is
# checked, as browsers commonly attach them to MediaRecorder uploads.
SUPPORTED_AUDIO_MEDIA_TYPES = frozenset({"audio/webm"})


class AudioUploadError(BaseModel):
    """Machine-readable error details for a rejected audio request."""

    code: str = Field(examples=["empty_audio_file"])
    message: str


class AudioUploadErrorResponse(BaseModel):
    """Consistent error envelope for the audio API."""

    error: AudioUploadError


class TranscriptionResponse(BaseModel):
    """Plain text returned by the speech-to-text provider.

    No vehicle or service fields are extracted at this boundary.
    """

    transcript: str


def audio_error_response(
    status_code: int,
    *,
    code: str,
    message: str,
) -> JSONResponse:
    """Build the documented JSON error envelope used by this route."""

    error = AudioUploadErrorResponse(
        error=AudioUploadError(code=code, message=message)
    )
    return JSONResponse(status_code=status_code, content=error.model_dump())


def _normalise_media_type(content_type: str | None) -> str | None:
    """Remove MIME parameters and normalise the comparable media type."""

    if content_type is None:
        return None
    media_type = content_type.split(";", maxsplit=1)[0].strip().lower()
    return media_type or None


@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Transcribe a recorded workshop audio note",
    responses={
        400: {"model": AudioUploadErrorResponse, "description": "Audio file missing."},
        415: {
            "model": AudioUploadErrorResponse,
            "description": "Audio format is not supported.",
        },
        422: {"model": AudioUploadErrorResponse, "description": "Audio file is empty."},
        502: {
            "model": AudioUploadErrorResponse,
            "description": "The transcription provider failed.",
        },
        503: {
            "model": AudioUploadErrorResponse,
            "description": "No transcription provider is configured.",
        },
    },
)
async def transcribe_workshop_audio(
    audio: Annotated[
        Optional[UploadFile], File(description="MediaRecorder audio file")
    ] = None,
    transcription_provider: Annotated[
        TranscriptionProvider, Depends(get_transcription_provider)
    ] = None,
) -> Union[TranscriptionResponse, JSONResponse]:
    """Validate a MediaRecorder upload and delegate speech-to-text work.

    Vehicle-data extraction deliberately does not happen here. The returned
    transcript will be a later input to a separate extraction workflow.
    """

    if audio is None:
        return audio_error_response(
            status.HTTP_400_BAD_REQUEST,
            code="audio_file_required",
            message="Eine Audiodatei muss im Feld 'audio' hochgeladen werden.",
        )

    media_type = _normalise_media_type(audio.content_type)
    if media_type not in SUPPORTED_AUDIO_MEDIA_TYPES:
        return audio_error_response(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            code="unsupported_audio_format",
            message="Nur Browseraufnahmen im Format audio/webm werden unterstützt.",
        )

    try:
        content = await audio.read()
    finally:
        await audio.close()

    if not content:
        return audio_error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="empty_audio_file",
            message="Die hochgeladene Audiodatei ist leer.",
        )

    recording = AudioRecording(
        content=content,
        media_type=media_type,
        filename=audio.filename or None,
    )
    try:
        transcript = await transcription_provider.transcribe(recording)
    except TranscriptionProviderUnavailableError as error:
        return audio_error_response(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            code="transcription_provider_unavailable",
            message=str(error),
        )
    except TranscriptionProviderError as error:
        return audio_error_response(
            status.HTTP_502_BAD_GATEWAY,
            code="transcription_failed",
            message=str(error),
        )

    return TranscriptionResponse(transcript=transcript)
