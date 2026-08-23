"""Durable local outbox for registration email deliveries.

The SMTP hand-off is inherently fallible.  This store writes the fully
validated registration before a delivery attempt starts, so a network or SMTP
failure cannot silently discard the mechanic's confirmed data.  SQLite keeps
the MVP dependency-free while still surviving process restarts when its file
is located on persistent storage.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Iterator, Optional
from uuid import UUID

from app.models.enums import ServiceStatus
from app.models.registration import RegistrationDraft


class DeliveryStoreError(RuntimeError):
    """Raised when the durable outbox cannot be read or updated."""


class DeliveryConflictError(RuntimeError):
    """Raised when an existing registration ID has different saved content."""


class DeliveryAlreadySentError(RuntimeError):
    """Raised when an already delivered record is claimed again."""


class DeliveryInProgressError(RuntimeError):
    """Raised when another request currently owns the delivery attempt."""


class DeliveryRecipientMissingError(RuntimeError):
    """Raised when no office recipient is available for a saved record."""


@dataclass(frozen=True)
class StoredDelivery:
    """One immutable registration payload and its mutable delivery metadata."""

    registration: RegistrationDraft
    status: ServiceStatus
    recipient: Optional[str]
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime]
    last_attempt_at: Optional[datetime]
    attempt_count: int
    last_error: Optional[str]

    @property
    def registration_id(self) -> UUID:
        return self.registration.id


class DeliveryStore:
    """SQLite-backed store with small, atomic state transitions."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def save_or_get(
        self,
        registration: RegistrationDraft,
        recipient: Optional[str],
    ) -> tuple[StoredDelivery, bool]:
        """Persist a registration once, or return its identical prior record.

        Reusing an ID with changed values is rejected.  That prevents a retry
        from accidentally sending a later browser draft under an older record
        ID and makes a successfully handled request idempotent.
        """

        # The transcript never belongs in the delivery email and project rules
        # keep it client-session-only.  Preserve every structured protocol
        # value needed for a retry without expanding that sensitive footprint.
        registration = registration.model_copy(
            deep=True,
            update={"raw_transcript": None},
        )
        payload = _serialize_registration(registration)
        now = _utc_now()
        try:
            with self._connection(write=True) as connection:
                row = connection.execute(
                    "SELECT * FROM deliveries WHERE registration_id = ?",
                    (str(registration.id),),
                ).fetchone()
                if row is not None:
                    if row["registration_json"] != payload:
                        raise DeliveryConflictError(
                            "Die Vorgangs-ID gehört bereits zu einem anderen gespeicherten Datensatz."
                        )
                    return self._to_delivery(row), False

                connection.execute(
                    """
                    INSERT INTO deliveries (
                        registration_id, registration_json, recipient, status,
                        created_at, updated_at, submitted_at, last_attempt_at,
                        attempt_count, last_error
                    ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, 0, NULL)
                    """,
                    (
                        str(registration.id),
                        payload,
                        recipient,
                        ServiceStatus.EMAIL_PENDING.value,
                        _serialize_datetime(now),
                        _serialize_datetime(now),
                    ),
                )
                row = connection.execute(
                    "SELECT * FROM deliveries WHERE registration_id = ?",
                    (str(registration.id),),
                ).fetchone()
                assert row is not None
                return self._to_delivery(row), True
        except DeliveryConflictError:
            raise
        except (OSError, sqlite3.Error, ValueError) as error:
            raise DeliveryStoreError(
                "Der Versandauftrag konnte nicht dauerhaft gespeichert werden."
            ) from error

    def get(self, registration_id: UUID) -> Optional[StoredDelivery]:
        """Return a saved record without exposing its payload to the caller."""

        try:
            with self._connection() as connection:
                row = connection.execute(
                    "SELECT * FROM deliveries WHERE registration_id = ?",
                    (str(registration_id),),
                ).fetchone()
                return self._to_delivery(row) if row is not None else None
        except (OSError, sqlite3.Error, ValueError) as error:
            raise DeliveryStoreError(
                "Der Versandstatus konnte nicht gelesen werden."
            ) from error

    def start_attempt(
        self,
        registration_id: UUID,
        fallback_recipient: Optional[str],
    ) -> StoredDelivery:
        """Atomically reserve a non-final record for one SMTP attempt."""

        now = _utc_now()
        try:
            with self._connection(write=True) as connection:
                row = connection.execute(
                    "SELECT * FROM deliveries WHERE registration_id = ?",
                    (str(registration_id),),
                ).fetchone()
                if row is None:
                    raise KeyError(registration_id)

                current = ServiceStatus(row["status"])
                if current is ServiceStatus.EMAIL_SENT:
                    raise DeliveryAlreadySentError(
                        "Der Vorgang wurde bereits erfolgreich versendet."
                    )
                if current is ServiceStatus.EMAIL_SENDING:
                    raise DeliveryInProgressError(
                        "Der Vorgang wird bereits versendet."
                    )

                recipient = row["recipient"] or fallback_recipient
                if not recipient:
                    raise DeliveryRecipientMissingError(
                        "CARTECH_OFFICE_EMAIL ist nicht konfiguriert."
                    )

                connection.execute(
                    """
                    UPDATE deliveries
                    SET recipient = ?, status = ?, updated_at = ?, last_attempt_at = ?,
                        attempt_count = attempt_count + 1, last_error = NULL
                    WHERE registration_id = ?
                    """,
                    (
                        recipient,
                        ServiceStatus.EMAIL_SENDING.value,
                        _serialize_datetime(now),
                        _serialize_datetime(now),
                        str(registration_id),
                    ),
                )
                updated = connection.execute(
                    "SELECT * FROM deliveries WHERE registration_id = ?",
                    (str(registration_id),),
                ).fetchone()
                assert updated is not None
                return self._to_delivery(updated)
        except (
            DeliveryAlreadySentError,
            DeliveryInProgressError,
            DeliveryRecipientMissingError,
            KeyError,
        ):
            raise
        except (OSError, sqlite3.Error, ValueError) as error:
            raise DeliveryStoreError(
                "Der Versandversuch konnte nicht sicher vorbereitet werden."
            ) from error

    def mark_sent(self, registration_id: UUID, submitted_at: datetime) -> StoredDelivery:
        """Mark a claimed record as accepted by the configured mail server."""

        return self._update_outcome(
            registration_id,
            status=ServiceStatus.EMAIL_SENT,
            submitted_at=submitted_at,
            last_error=None,
        )

    def mark_failed(self, registration_id: UUID, error_message: str) -> StoredDelivery:
        """Preserve a safe error message and leave the record retryable."""

        return self._update_outcome(
            registration_id,
            status=ServiceStatus.EMAIL_FAILED,
            submitted_at=None,
            last_error=error_message,
        )

    def recover_interrupted_attempts(self) -> int:
        """Make attempts left in progress by a stopped process retryable again."""

        now = _utc_now()
        message = (
            "Der Dienst wurde während eines Versandversuchs beendet. "
            "Der Vorgang kann erneut versendet werden."
        )
        try:
            with self._connection(write=True) as connection:
                cursor = connection.execute(
                    """
                    UPDATE deliveries
                    SET status = ?, updated_at = ?, last_error = ?
                    WHERE status = ?
                    """,
                    (
                        ServiceStatus.EMAIL_FAILED.value,
                        _serialize_datetime(now),
                        message,
                        ServiceStatus.EMAIL_SENDING.value,
                    ),
                )
                return cursor.rowcount
        except (OSError, sqlite3.Error) as error:
            raise DeliveryStoreError(
                "Unterbrochene Versandversuche konnten nicht wiederhergestellt werden."
            ) from error

    def _update_outcome(
        self,
        registration_id: UUID,
        *,
        status: ServiceStatus,
        submitted_at: Optional[datetime],
        last_error: Optional[str],
    ) -> StoredDelivery:
        now = _utc_now()
        try:
            with self._connection(write=True) as connection:
                cursor = connection.execute(
                    """
                    UPDATE deliveries
                    SET status = ?, updated_at = ?, submitted_at = ?, last_error = ?
                    WHERE registration_id = ?
                    """,
                    (
                        status.value,
                        _serialize_datetime(now),
                        _serialize_datetime(submitted_at) if submitted_at else None,
                        last_error,
                        str(registration_id),
                    ),
                )
                if cursor.rowcount != 1:
                    raise KeyError(registration_id)
                row = connection.execute(
                    "SELECT * FROM deliveries WHERE registration_id = ?",
                    (str(registration_id),),
                ).fetchone()
                assert row is not None
                return self._to_delivery(row)
        except KeyError:
            raise
        except (OSError, sqlite3.Error, ValueError) as error:
            raise DeliveryStoreError(
                "Der Versandstatus konnte nicht dauerhaft aktualisiert werden."
            ) from error

    @contextmanager
    def _connection(self, *, write: bool = False) -> Iterator[sqlite3.Connection]:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self._path, timeout=10)
            connection.row_factory = sqlite3.Row
            self._ensure_schema(connection)
            if write:
                connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
            except BaseException:
                connection.rollback()
                raise
            else:
                connection.commit()
            finally:
                connection.close()
        except (OSError, sqlite3.Error):
            raise

    @staticmethod
    def _ensure_schema(connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS deliveries (
                registration_id TEXT PRIMARY KEY,
                registration_json TEXT NOT NULL,
                recipient TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                submitted_at TEXT,
                last_attempt_at TEXT,
                attempt_count INTEGER NOT NULL CHECK (attempt_count >= 0),
                last_error TEXT
            )
            """
        )

    @staticmethod
    def _to_delivery(row: sqlite3.Row) -> StoredDelivery:
        return StoredDelivery(
            registration=RegistrationDraft.model_validate_json(row["registration_json"]),
            status=ServiceStatus(row["status"]),
            recipient=row["recipient"],
            created_at=_parse_datetime(row["created_at"]),
            updated_at=_parse_datetime(row["updated_at"]),
            submitted_at=_parse_datetime(row["submitted_at"])
            if row["submitted_at"]
            else None,
            last_attempt_at=_parse_datetime(row["last_attempt_at"])
            if row["last_attempt_at"]
            else None,
            attempt_count=row["attempt_count"],
            last_error=row["last_error"],
        )


def _serialize_registration(registration: RegistrationDraft) -> str:
    return json.dumps(
        registration.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _serialize_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
