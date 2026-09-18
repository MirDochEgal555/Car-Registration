"""Tests for the Phase 7 German workshop-extraction prompt contract."""

from __future__ import annotations

from app.models.extraction import structured_extraction_json_schema
from app.services.extraction import (
    GERMAN_WORKSHOP_EXTRACTION_PROMPT,
    STRUCTURED_EXTRACTION_SCHEMA_NAME,
    build_german_workshop_extraction_prompt,
    structured_extraction_response_format,
)


def test_prompt_covers_the_required_workshop_extraction_topics() -> None:
    """Protect core extraction rules against accidental prompt shortening."""

    for term in (
        "Kennzeichen",
        "Kilometerstände",
        "Reifenart",
        "Reifengrößen",
        "Hersteller",
        "Modell",
        "Anzahl",
        "Profiltiefen",
        "Positionen",
        "Reifenzustände",
        "Servicehinweise",
        "Korrektur",
        "Widerspruch",
        "uncertain",
        "ausschließlich Füllwörter",
    ):
        assert term in GERMAN_WORKSHOP_EXTRACTION_PROMPT


def test_prompt_forbids_inference_and_backend_validation() -> None:
    """Extraction must not absorb the later validation responsibility."""

    assert "Ergänze niemals" in GERMAN_WORKSHOP_EXTRACTION_PROMPT
    assert "rate nicht" in GERMAN_WORKSHOP_EXTRACTION_PROMPT
    assert "Backend-Validierung" in GERMAN_WORKSHOP_EXTRACTION_PROMPT
    assert "Plausibilitäts" in GERMAN_WORKSHOP_EXTRACTION_PROMPT


def test_prompt_covers_filler_words_spoken_values_and_scoped_corrections() -> None:
    """Natural workshop speech must be resolved without extending its facts."""

    for term in (
        "Füllwörter",
        "gesprochene Zahlenwörter",
        "Dezimalzahlen",
        "CW AB eins zwei drei",
        "225, 45, 17",
        "Vorderachse",
        "Hinterachse",
        "mehreren in einer Aussage genannten Reifen",
        "Modell weiß ich",
        "äh nein, hinten auch vier",
    ):
        assert term in GERMAN_WORKSHOP_EXTRACTION_PROMPT

    assert "nicht gemittelt oder angeglichen" in GERMAN_WORKSHOP_EXTRACTION_PROMPT
    assert "`model` fehlend" in GERMAN_WORKSHOP_EXTRACTION_PROMPT


def test_prompt_keeps_transcript_verbatim_and_delimited() -> None:
    """Caller-supplied workshop text is data, not an instruction replacement."""

    transcript = "Hinten drei Millimeter, nein, vier Millimeter."

    prompt = build_german_workshop_extraction_prompt(transcript)

    assert prompt.startswith(GERMAN_WORKSHOP_EXTRACTION_PROMPT)
    assert "--- BEGINN DES TRANSKRIPTS (NUR DATEN) ---" in prompt
    assert transcript in prompt
    assert prompt.endswith("--- ENDE DES TRANSKRIPTS ---")


def test_response_format_reuses_the_central_strict_schema() -> None:
    """The OpenAI request uses the central schema without invalid ref metadata."""

    response_format = structured_extraction_response_format()

    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["name"] == STRUCTURED_EXTRACTION_SCHEMA_NAME
    assert response_format["json_schema"]["strict"] is True
    assert response_format["json_schema"]["schema"] != structured_extraction_json_schema()

    def assert_ref_objects_are_clean(value: object) -> None:
        if isinstance(value, dict):
            if "$ref" in value:
                assert set(value) == {"$ref"}
            for nested in value.values():
                assert_ref_objects_are_clean(nested)
        elif isinstance(value, list):
            for nested in value:
                assert_ref_objects_are_clean(nested)

    assert_ref_objects_are_clean(response_format["json_schema"]["schema"])
