from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.v1.routes.audio import get_transcription_provider
from app.main import app
from app.services.transcription import AudioRecording


class RecordingTranscriptionProvider:
    """Speech-to-text double that verifies the API/provider boundary."""

    def __init__(self) -> None:
        self.recordings: list[AudioRecording] = []

    async def transcribe(self, recording: AudioRecording) -> str:
        self.recordings.append(recording)
        return "Werkstattnotiz"


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
    assert response.json() == {"transcript": "Werkstattnotiz"}
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
    assert response.json()["error"]["code"] == "unsupported_audio_format"


def test_rejects_empty_audio_upload() -> None:
    response = TestClient(app).post(
        "/api/v1/audio/transcribe",
        files={"audio": ("workshop-note.webm", b"", "audio/webm")},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "empty_audio_file"


def test_returns_structured_error_when_no_provider_is_configured() -> None:
    response = TestClient(app).post(
        "/api/v1/audio/transcribe",
        files={"audio": ("workshop-note.webm", b"audio", "audio/webm")},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "transcription_provider_unavailable"
