"""OpenAI adapter for strict workshop-data extraction.

The provider boundary returns the raw JSON object required by the existing
``StructuredExtractionResult`` contract.  Normalisation, deterministic
validation and mapping deliberately happen after this boundary, so a model
response can never bypass the Phase-7 safeguards.
"""

from __future__ import annotations

import inspect
import json
import logging
from collections.abc import Mapping
from typing import Any, Protocol

from app.core.config import settings
from app.services.extraction import (
    build_german_workshop_extraction_prompt,
    structured_extraction_response_format,
)


logger = logging.getLogger(__name__)

DEFAULT_OPENAI_EXTRACTION_MODEL = "gpt-4o-mini"


class ExtractionProvider(Protocol):
    """Minimal, injectable contract for transcript-to-JSON extraction."""

    async def extract(self, transcript: str) -> Mapping[str, Any]:
        """Return one raw object matching the strict Structured-Output schema."""


class ExtractionProviderError(RuntimeError):
    """Raised when a configured provider cannot produce usable JSON."""


class ExtractionProviderUnavailableError(ExtractionProviderError):
    """Raised when no configured extraction provider is available."""


class UnconfiguredExtractionProvider:
    """Safe default that never fabricates extraction data without a provider."""

    async def extract(self, transcript: str) -> Mapping[str, Any]:
        del transcript
        raise ExtractionProviderUnavailableError(
            "Für die KI-Extraktion ist kein OpenAI-API-Schlüssel konfiguriert."
        )


class OpenAIStructuredExtractionProvider:
    """Request a strict JSON object from the configured OpenAI chat model."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = DEFAULT_OPENAI_EXTRACTION_MODEL,
        timeout_seconds: float = 30.0,
        client: Any | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        # Injection keeps the integration testable without an external call.
        self._client = client

    async def extract(self, transcript: str) -> Mapping[str, Any]:
        """Return the unmodified JSON object from a Structured-Outputs call."""

        client = self._client
        created_client = client is None
        try:
            if client is None:
                client = self._create_client()
            response = await client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "user",
                        "content": build_german_workshop_extraction_prompt(transcript),
                    }
                ],
                response_format=structured_extraction_response_format(),
            )
            content = _response_content(response)
            payload = json.loads(content)
        except ExtractionProviderError:
            raise
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            logger.warning(
                "OpenAI extraction returned no usable strict JSON (%s).",
                type(error).__name__,
            )
            raise ExtractionProviderError(
                "Die KI-Extraktion hat keine verwertbare strukturierte Antwort geliefert."
            ) from error
        except Exception as error:
            logger.warning(
                "OpenAI extraction request failed (%s).", type(error).__name__
            )
            if _is_openai_service_unavailable(error):
                raise ExtractionProviderUnavailableError(
                    "Der KI-Extraktionsdienst ist zurzeit nicht verfügbar."
                ) from error
            raise ExtractionProviderError(
                "Die KI-Extraktion ist fehlgeschlagen. Bitte erneut versuchen."
            ) from error
        finally:
            if created_client and client is not None:
                await _close_client(client)

        if not isinstance(payload, dict):
            raise ExtractionProviderError(
                "Die KI-Extraktion hat kein strukturiertes Objekt geliefert."
            )
        return payload

    def _create_client(self) -> Any:
        """Create the SDK client lazily so an unconfigured app can start."""

        try:
            from openai import AsyncOpenAI
        except ImportError as error:
            raise ExtractionProviderUnavailableError(
                "Der OpenAI-KI-Extraktionsdienst ist nicht installiert."
            ) from error
        return AsyncOpenAI(
            api_key=self._api_key,
            timeout=self._timeout_seconds,
            max_retries=0,
        )


def get_extraction_provider() -> ExtractionProvider:
    """Supply the configured provider without making an eager network call."""

    if settings.openai_api_key is None:
        return UnconfiguredExtractionProvider()
    return OpenAIStructuredExtractionProvider(
        api_key=settings.openai_api_key,
        model=settings.openai_extraction_model,
        timeout_seconds=settings.openai_timeout_seconds,
    )


def _response_content(response: object) -> str:
    """Read the single strict JSON message without accepting partial choices."""

    choices = getattr(response, "choices", None)
    if not isinstance(choices, list) or len(choices) != 1:
        raise ExtractionProviderError(
            "Die KI-Extraktion hat keine eindeutige Antwort geliefert."
        )
    content = getattr(getattr(choices[0], "message", None), "content", None)
    if not isinstance(content, str) or not content.strip():
        raise ExtractionProviderError(
            "Die KI-Extraktion hat keine strukturierte Antwort geliefert."
        )
    return content


def _is_openai_service_unavailable(error: Exception) -> bool:
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
    """Release a request-local SDK client without masking the response."""

    close = getattr(client, "close", None)
    if not callable(close):
        return
    try:
        result = close()
        if inspect.isawaitable(result):
            await result
    except Exception:
        logger.warning("Could not close the OpenAI extraction client.")


__all__ = [
    "DEFAULT_OPENAI_EXTRACTION_MODEL",
    "ExtractionProvider",
    "ExtractionProviderError",
    "ExtractionProviderUnavailableError",
    "OpenAIStructuredExtractionProvider",
    "UnconfiguredExtractionProvider",
    "get_extraction_provider",
]
