"""Regression corpus for German workshop speech-to-text.

These tests deliberately mock the external transcription model. They verify
that every realistic workshop utterance reaches the provider with German
automotive context and that its raw text is returned without local
normalisation. Acoustic recognition itself is exercised by the documented
manual run using the same corpus.
"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import pytest

from app.services.transcription import (
    AudioRecording,
    GERMAN_AUTOMOTIVE_KEYWORDS,
    GERMAN_AUTOMOTIVE_TRANSCRIPTION_PROMPT,
    OpenAITranscriptionProvider,
)


_FIXTURE_PATH = (
    Path(__file__).parents[3] / "data/fixtures/german_workshop_stt_cases.json"
)


class FakeOpenAITranscriptions:
    """Record one request and return a fixture-defined raw transcript."""

    def __init__(self, transcript: str) -> None:
        self._transcript = transcript
        self.requests: list[dict[str, object]] = []

    async def create(self, **request: object):
        self.requests.append(request)
        return type("Transcription", (), {"text": self._transcript})()


class FakeOpenAIClient:
    def __init__(self, transcript: str) -> None:
        transcriptions = FakeOpenAITranscriptions(transcript)
        self.audio = type("Audio", (), {"transcriptions": transcriptions})()


def _load_cases() -> list[dict[str, object]]:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


GERMAN_WORKSHOP_STT_CASES = _load_cases()


def test_german_workshop_stt_corpus_covers_required_workshop_language() -> None:
    """Keep the corpus focused on the terms that routinely confuse STT."""

    corpus = "\n".join(
        str(case["expected_transcript"]) for case in GERMAN_WORKSHOP_STT_CASES
    )

    assert re.search(r"\b[A-Z]{1,3}-[A-Z]{1,2} \d{1,4}\b", corpus)
    assert re.search(r"\b\d{1,3}\.\d{3}\b", corpus)
    assert "205/55 R16" in corpus
    assert "225/40 R18" in corpus
    assert "63.500 Kilometer" in corpus
    assert "6.350 Kilometer" in corpus
    assert "Millimeter" in corpus
    assert {"Michelin", "Continental", "Goodyear", "Bridgestone", "Hankook"} <= set(
        corpus.replace(";", "").replace(",", "").split()
    )
    for term in (
        "Pilot Sport 5",
        "WinterContact TS 870",
        "Vector 4Seasons Gen-3",
        "Blizzak LM005",
        "Ventus Prime 4",
        "Alpin 6",
        "Vorderachse",
        "Hinterachse",
        "vorne",
        "hinten",
        "links",
        "rechts",
    ):
        assert term in corpus


def test_numeric_cases_keep_plate_mileage_size_and_wheel_value_pairs_distinct() -> None:
    """Guard the exact numeric pairs that are easy to confuse acoustically."""

    cases_by_id = {str(case["id"]): case for case in GERMAN_WORKSHOP_STT_CASES}

    assert cases_by_id["07-numeric-plate-63500-and-205-55-r16"][
        "required_fragments"
    ] == ["M-AB 6350", "63.500 Kilometer", "205/55 R16"]
    assert cases_by_id["08-numeric-plate-6350-and-225-40-r18"][
        "required_fragments"
    ] == ["M-AB 6350", "6.350 Kilometer", "225/40 R18"]
    assert cases_by_id["09-numeric-tread-depths-by-wheel-position"][
        "required_fragments"
    ] == [
        "vorne links 4,5",
        "vorne rechts 5,4",
        "hinten links 5,4",
        "hinten rechts 4,5",
    ]


@pytest.mark.parametrize(
    "case", GERMAN_WORKSHOP_STT_CASES, ids=lambda case: str(case["id"])
)
def test_german_workshop_transcript_is_sent_with_context_and_preserved(
    case: dict[str, object],
) -> None:
    """Exercise each natural-language case without making an external request."""

    expected_transcript = str(case["expected_transcript"])
    client = FakeOpenAIClient(expected_transcript)
    provider = OpenAITranscriptionProvider(api_key="not-a-real-secret", client=client)

    transcript = asyncio.run(
        provider.transcribe(
            AudioRecording(
                content=f"recording for {case['id']}".encode(),
                media_type="audio/webm",
                filename=f"{case['id']}.webm",
            )
        )
    )

    assert transcript == expected_transcript
    for fragment in case["required_fragments"]:
        assert str(fragment).casefold() in transcript.casefold()

    request = client.audio.transcriptions.requests[0]
    assert request["language"] == "de"
    assert request["prompt"] == GERMAN_AUTOMOTIVE_TRANSCRIPTION_PROMPT
    assert request["keywords"] == list(GERMAN_AUTOMOTIVE_KEYWORDS)


@pytest.mark.parametrize(
    ("case_id", "documented_result"),
    [
        pytest.param(
            str(case["id"]),
            result,
            id=f"{case['id']}-{result['classification']}",
        )
        for case in GERMAN_WORKSHOP_STT_CASES
        for result in case.get("documented_raw_results", [])
    ],
)
def test_documented_incorrect_or_ambiguous_results_are_never_corrected(
    case_id: str, documented_result: dict[str, object]
) -> None:
    """Return problematic provider text as-is for later human review."""

    raw_result = str(documented_result["provider_transcript"])
    client = FakeOpenAIClient(raw_result)
    provider = OpenAITranscriptionProvider(api_key="not-a-real-secret", client=client)

    transcript = asyncio.run(
        provider.transcribe(
            AudioRecording(
                content=f"recording for {case_id}".encode(),
                media_type="audio/webm",
                filename=f"{case_id}.webm",
            )
        )
    )

    assert documented_result["classification"] in {"incorrect", "ambiguous"}
    assert isinstance(documented_result["reason"], str)
    assert transcript == raw_result
    expected_transcript = next(
        str(case["expected_transcript"])
        for case in GERMAN_WORKSHOP_STT_CASES
        if case["id"] == case_id
    )
    assert transcript != expected_transcript


def test_transcription_context_explicitly_names_german_workshop_entities() -> None:
    """Avoid silently losing key terminology when the prompt is edited."""

    for term in (
        "Kennzeichen",
        "Kilometerstände",
        "Reifengrößen",
        "Marken",
        "Modellbezeichnungen",
        "Profiltiefe",
        "Vorderachse",
        "Hinterachse",
        "vorne links",
        "vorne rechts",
        "hinten links",
        "hinten rechts",
    ):
        assert term in GERMAN_AUTOMOTIVE_TRANSCRIPTION_PROMPT

    assert {
        "Kennzeichen",
        "Kilometerstand",
        "205/55 R16",
        "225/40 R18",
        "Michelin",
        "Continental",
        "Goodyear",
        "Bridgestone",
        "Hankook",
    } <= set(GERMAN_AUTOMOTIVE_KEYWORDS)
