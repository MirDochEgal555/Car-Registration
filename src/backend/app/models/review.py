"""Shared rules for deriving a service record's review requirement."""

from __future__ import annotations

from collections.abc import Mapping

from app.models.enums import FieldStatus


REVIEW_REQUIRED_FIELD_STATUSES = frozenset(
    {FieldStatus.UNCERTAIN, FieldStatus.INVALID}
)
"""Field statuses that require a mechanic or office review."""


def calculate_review_required(
    field_status: Mapping[str, FieldStatus] | None,
) -> bool:
    """Return whether any field status requires review.

    Missing optional information is visible to downstream consumers but does
    not by itself require review.  `valid` entries make the extraction result
    explicit without affecting the review flag.
    """

    return bool(
        field_status
        and REVIEW_REQUIRED_FIELD_STATUSES.intersection(field_status.values())
    )
