from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from app.api.v1.routes.audio import get_transcription_provider
from app.core.config import Settings
from app.main import app
import app.services.transcription as transcription_service
from app.services.transcription import (
    AudioRecording,
    GERMAN_AUTOMOTIVE_KEYWORDS,
    GERMAN_AUTOMOTIVE_TRANSCRIPTION_PROMPT,
    OpenAITranscriptionProvider,
    TranscriptionProviderError,
)


class RecordingTranscriptionProvider:
    """Speech-to-text double that verifies the API/provider boundary."""

    def __init__(self) -> None:
        self.recordings: list[AudioRecording] = []

    async def transcribe(self, recording: AudioRecording) -> str:
        self.recordings.append(recording)
        return "Werkstattnotiz"


class FailingTranscriptionProvider:
    async def transcribe(self, recording: AudioRecording) -> str:
        del recording
        raise TranscriptionProviderError("Der Transkriptionsdienst hat abgelehnt.")


class UnexpectedlyFailingTranscriptionProvider:
    async def transcribe(self, recording: AudioRecording) -> str:
        del recording
        raise RuntimeError("upstream diagnostic that must not reach the client")


class FakeOpenAITranscriptions:
    def __init__(self) -> None:
        self.requests: list[dict[str, object]] = []

    async def create(self, **request: object):
        self.requests.append(request)
        return type("Transcription", (), {"text": "  Audi A4, RDKS geprüft.  "})()


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.transcriptions = FakeOpenAITranscriptions()
        self.audio = type("Audio", (), {"transcriptions": self.transcriptions})()


def test_transcribes_a_webm_mediarecorder_upload() -> None:
    provider = RecordingTranscriptionProvider()
    app.dependency_overrides[get_transcription_provider] = lambda: provider
    try:
        response = TestClient(app).post(
            "/api/v1/audio/transcribe",
            files={
                "audio": (
                    "workshop-note.webm",
                    b"recorded workshop audio",
                    "audio/webm;codecs=opus",
                )
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "completed",
        "transcript": "Werkstattnotiz",
    }
    assert provider.recordings == [
        AudioRecording(
            content=b"recorded workshop audio",
            media_type="audio/webm",
            filename="workshop-note.webm",
        )
    ]


def test_rejects_request_without_an_audio_file() -> None:
    response = TestClient(app).post("/api/v1/audio/transcribe")

    assert response.status_code == 400
    assert response.json() == {
        "status": "failed",
        "transcript": None,
        "error": {
            "code": "audio_file_required",
            "message": "Eine Audiodatei muss im Feld 'audio' hochgeladen werden.",
        }
    }


def test_rejects_a_non_file_audio_field_with_a_structured_error() -> None:
    response = TestClient(app).post(
        "/api/v1/audio/transcribe",
        data={"audio": "not-an-audio-file"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "status": "failed",
        "transcript": None,
        "error": {
            "code": "invalid_audio_upload",
            "message": "Im Feld 'audio' muss eine Audiodatei hochgeladen werden.",
        }
    }


def test_rejects_unsupported_audio_format() -> None:
    response = TestClient(app).post(
        "/api/v1/audio/transcribe",
        files={"audio": ("workshop-note.wav", b"audio", "audio/wav")},
    )

    assert response.status_code == 415
    assert response.json()["status"] == "failed"
    assert response.json()["error"]["code"] == "unsupported_audio_format"


def test_rejects_empty_audio_upload() -> None:
    response = TestClient(app).post(
        "/api/v1/audio/transcribe",
        files={"audio": ("workshop-note.webm", b"", "audio/webm")},
    )

    assert response.status_code == 422
    assert response.json()["status"] == "failed"
    assert response.json()["error"]["code"] == "empty_audio_file"


def test_returns_structured_error_when_no_provider_is_configured() -> None:
    response = TestClient(app).post(
        "/api/v1/audio/transcribe",
        files={"audio": ("workshop-note.webm", b"audio", "audio/webm")},
    )

    assert response.status_code == 503
    assert response.json()["status"] == "failed"
    assert response.json()["error"]["code"] == "transcription_provider_unavailable"


def test_returns_failed_status_and_error_when_transcription_fails() -> None:
    app.dependency_overrides[get_transcription_provider] = FailingTranscriptionProvider
    try:
        response = TestClient(app).post(
            "/api/v1/audio/transcribe",
            files={"audio": ("workshop-note.webm", b"audio", "audio/webm")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json() == {
        "status": "failed",
        "transcript": None,
        "error": {
            "code": "transcription_failed",
            "message": "Der Transkriptionsdienst hat abgelehnt.",
        },
    }


def test_keeps_unexpected_provider_failures_in_the_documented_error_shape() -> None:
    app.dependency_overrides[get_transcription_provider] = (
        UnexpectedlyFailingTranscriptionProvider
    )
    try:
        response = TestClient(app).post(
            "/api/v1/audio/transcribe",
            files={"audio": ("workshop-note.webm", b"audio", "audio/webm")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json() == {
        "status": "failed",
        "transcript": None,
        "error": {
            "code": "transcription_failed",
            "message": "Die Sprachtranskription ist fehlgeschlagen. Bitte erneut versuchen.",
        },
    }


def test_openai_provider_uses_german_workshop_context_without_extracting_fields() -> None:
    client = FakeOpenAIClient()
    provider = OpenAITranscriptionProvider(api_key="not-a-real-secret", client=client)

    transcript = asyncio.run(
        provider.transcribe(
            AudioRecording(
                content=b"recorded workshop audio",
                media_type="audio/webm",
                filename="workshop-note.webm",
            )
        )
    )

    assert transcript == "Audi A4, RDKS geprüft."
    assert client.transcriptions.requests == [
        {
            "file": ("workshop-note.webm", b"recorded workshop audio", "audio/webm"),
            "model": "gpt-transcribe",
            "language": "de",
            "prompt": GERMAN_AUTOMOTIVE_TRANSCRIPTION_PROMPT,
            "keywords": list(GERMAN_AUTOMOTIVE_KEYWORDS),
        }
    ]


def test_get_transcription_provider_uses_the_configured_openai_adapter(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        transcription_service,
        "settings",
        Settings(
            openai_api_key="not-a-real-secret",
            openai_transcription_model="gpt-transcribe",
            openai_timeout_seconds=12.0,
        ),
    )

    provider = transcription_service.get_transcription_provider()

    assert isinstance(provider, OpenAITranscriptionProvider)
