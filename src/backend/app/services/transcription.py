"""Speech-to-text adapters for workshop recordings.

The API layer only knows how to validate an uploaded recording and pass it to
this module. The adapter returns plain text only: turning a transcript into
vehicle or service fields deliberately belongs to a later workflow.
"""

from __future__ import annotations

from dataclasses import dataclass
import inspect
import logging
from pathlib import Path
from typing import Any, Protocol

from app.core.config import settings


logger = logging.getLogger(__name__)

DEFAULT_OPENAI_TRANSCRIPTION_MODEL = "gpt-transcribe"

# ``gpt-transcribe`` accepts both unstructured context and keyword hints. The
# prompt is intentionally in German, matching the recording language, and
# limits the job to transcription rather than the later data-extraction step.
GERMAN_AUTOMOTIVE_TRANSCRIPTION_PROMPT = (
    "Dies ist eine deutschsprachige Sprachnotiz aus einer Kfz-Werkstatt. "
    "Transkribiere vollständig und möglichst wortgetreu. Keine Zusammenfassung, "
    "keine Interpretation, keine Korrektur und keine Strukturierung in Fahrzeug- "
    "oder Servicefelder. Kennzeichen, Kilometerstände, Messwerte, Reifengrößen, "
    "DOT-Codes, Marken, Modellbezeichnungen und Radpositionen exakt beibehalten. "
    "Fachbegriffe sind zum Beispiel Reifenwechsel, Reifeneinlagerung, "
    "Sommerreifen, Winterreifen, Ganzjahresreifen, Felge, Profiltiefe, Luftdruck, "
    "RDKS, Bremsen, Radschrauben, Drehmoment, Wuchtgewichte, HU, AU, "
    "vorne links, vorne rechts, hinten links und hinten rechts."
)

GERMAN_AUTOMOTIVE_KEYWORDS = (
    "Reifenwechsel",
    "Reifeneinlagerung",
    "Sommerreifen",
    "Winterreifen",
    "Ganzjahresreifen",
    "Profiltiefe",
    "Luftdruck",
    "RDKS",
    "Reifendruckkontrollsystem",
    "Radschrauben",
    "Drehmoment",
    "Wuchtgewichte",
    "Felgen",
    "Bremsen",
    "HU",
    "AU",
    "DOT",
)


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
            "Für die Sprachtranskription ist kein OpenAI-API-Schlüssel konfiguriert."
        )


class OpenAITranscriptionProvider:
    """Transcribe a completed browser recording with OpenAI's file API."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = DEFAULT_OPENAI_TRANSCRIPTION_MODEL,
        timeout_seconds: float = 30.0,
        client: Any | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        # Injection keeps the provider unit-testable without contacting OpenAI.
        self._client = client

    async def transcribe(self, recording: AudioRecording) -> str:
        """Return the German workshop transcript from a validated WebM upload."""

        request: dict[str, Any] = {
            "file": (
                _transcription_filename(recording),
                recording.content,
                recording.media_type,
            ),
            "model": self._model,
            "language": "de",
            "prompt": GERMAN_AUTOMOTIVE_TRANSCRIPTION_PROMPT,
        }
        # Keyword hints are a ``gpt-transcribe`` feature. The prompt and German
        # language hint still provide workshop context if deployment overrides
        # the model with another compatible transcription model.
        if self._model == DEFAULT_OPENAI_TRANSCRIPTION_MODEL:
            request["keywords"] = list(GERMAN_AUTOMOTIVE_KEYWORDS)

        client = self._client
        created_client = client is None
        try:
            if client is None:
                client = self._create_client()
            response = await client.audio.transcriptions.create(**request)
        except TranscriptionProviderError:
            raise
        except Exception as error:
            logger.warning(
                "OpenAI transcription request failed (%s).", type(error).__name__
            )
            if _is_openai_service_unavailable(error):
                raise TranscriptionProviderUnavailableError(
                    "Der Sprachtranskriptionsdienst ist zurzeit nicht verfügbar."
                ) from error
            raise TranscriptionProviderError(
                "Die Sprachtranskription ist fehlgeschlagen. Bitte erneut versuchen."
            ) from error
        finally:
            if created_client and client is not None:
                await _close_client(client)

        transcript = getattr(response, "text", None)
        if not isinstance(transcript, str) or not transcript.strip():
            raise TranscriptionProviderError(
                "Der Sprachtranskriptionsdienst hat keinen Text zurückgegeben."
            )
        return transcript.strip()

    def _create_client(self) -> Any:
        """Create the async SDK lazily so an unconfigured app can still start."""

        try:
            from openai import AsyncOpenAI
        except ImportError as error:
            raise TranscriptionProviderUnavailableError(
                "Der OpenAI-Sprachtranskriptionsdienst ist nicht installiert."
            ) from error
        return AsyncOpenAI(
            api_key=self._api_key,
            timeout=self._timeout_seconds,
            max_retries=0,
        )


def _transcription_filename(recording: AudioRecording) -> str:
    """Return a safe extension-bearing name, as required by file transcription."""

    filename = Path(recording.filename or "workshop-notiz.webm").name
    if not filename.lower().endswith(".webm"):
        filename = f"{filename}.webm"
    return filename


def _is_openai_service_unavailable(error: Exception) -> bool:
    """Classify retryable provider failures without exposing provider internals."""

    if getattr(error, "status_code", None) in {401, 403, 429, 500, 502, 503, 504}:
        return True
    return type(error).__name__ in {
        "APIConnectionError",
        "APITimeoutError",
        "AuthenticationError",
        "InternalServerError",
        "PermissionDeniedError",
        "RateLimitError",
    }


async def _close_client(client: Any) -> None:
    """Release a per-request SDK client without masking transcription results."""

    close = getattr(client, "close", None)
    if not callable(close):
        return
    try:
        result = close()
        if inspect.isawaitable(result):
            await result
    except Exception:
        logger.warning("Could not close the OpenAI transcription client.")


def get_transcription_provider() -> TranscriptionProvider:
    """Supply the configured speech-to-text provider to API routes."""

    if settings.openai_api_key is None:
        return UnconfiguredTranscriptionProvider()
    return OpenAITranscriptionProvider(
        api_key=settings.openai_api_key,
        model=settings.openai_transcription_model,
        timeout_seconds=settings.openai_timeout_seconds,
    )
