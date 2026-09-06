"""Provider boundary for converting workshop recordings to plain text.

The API layer only knows how to validate an uploaded recording and pass it to
this contract. A concrete speech-to-text adapter can be added later without
coupling it to FastAPI or to vehicle-data extraction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AudioRecording:
    """A validated in-memory browser recording for a transcription provider."""

    content: bytes
    media_type: str
    filename: str | None


class TranscriptionProvider(Protocol):
    """Minimal contract implemented by speech-to-text providers."""

    async def transcribe(self, recording: AudioRecording) -> str:
        """Return only the spoken transcript for a validated recording."""


class TranscriptionProviderError(RuntimeError):
    """Raised when a configured provider cannot transcribe a recording."""


class TranscriptionProviderUnavailableError(TranscriptionProviderError):
    """Raised while no speech-to-text provider has been configured."""


class UnconfiguredTranscriptionProvider:
    """Safe default until a speech-to-text integration is selected."""

    async def transcribe(self, recording: AudioRecording) -> str:
        del recording
        raise TranscriptionProviderUnavailableError(
            "Für die Sprachtranskription ist noch kein Anbieter konfiguriert."
        )


def get_transcription_provider() -> TranscriptionProvider:
    """Supply the current speech-to-text provider to API routes.

    Keeping this dependency here makes it straightforward to replace in an
    application factory or in tests, while future provider credentials and
    request logic stay out of the route module.
    """

    return UnconfiguredTranscriptionProvider()
