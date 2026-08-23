"""Enumerations defined by documentation/DATA_MODEL.md."""

from enum import Enum


class StrEnum(str, Enum):
    """String-backed enums serialize to their documented API values."""


class PropulsionType(StrEnum):
    ELECTRIC = "electric"
    HYBRID = "hybrid"
    OTHER = "other"
    UNKNOWN = "unknown"


class ServiceType(StrEnum):
    TIRE_CHANGE = "tire_change"
    TIRE_STORAGE = "tire_storage"


class ServiceStatus(StrEnum):
    DRAFT = "draft"
    MECHANIC_REVIEW = "mechanic_review"
    EMAIL_PENDING = "email_pending"
    EMAIL_SENDING = "email_sending"
    EMAIL_SENT = "email_sent"
    EMAIL_FAILED = "email_failed"
    NEW = "new"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    REJECTED = "rejected"


class FieldStatus(StrEnum):
    MISSING = "missing"
    UNCERTAIN = "uncertain"
    INVALID = "invalid"
    VALID = "valid"


class WheelBoltConfiguration(StrEnum):
    SAME = "same"
    DIFFERENT = "different"
    UNKNOWN = "unknown"


class InspectionResult(StrEnum):
    OK = "ok"
    NOT_OK = "not_ok"
    UNKNOWN = "unknown"


class VisualInspectionResult(StrEnum):
    OK = "ok"
    NOT_OK = "not_ok"


class RdksType(StrEnum):
    ACTIVE = "active"
    PASSIVE = "passive"
    UNKNOWN = "unknown"


class TireType(StrEnum):
    SUMMER = "summer"
    WINTER = "winter"
    ALL_SEASON = "all_season"
    UNKNOWN = "unknown"


class RimCategory(StrEnum):
    ALLOY = "alloy"
    STEEL = "steel"
    ORIGINAL = "original"
    UNKNOWN = "unknown"


class TireSetRole(StrEnum):
    INSTALLED = "installed"
    REMOVED = "removed"
    STORED = "stored"


class TirePosition(StrEnum):
    FRONT_LEFT = "front_left"
    FRONT_RIGHT = "front_right"
    REAR_LEFT = "rear_left"
    REAR_RIGHT = "rear_right"
    FRONT = "front"
    REAR = "rear"
    ALL = "all"
    UNKNOWN = "unknown"


class VisualInspectionComponent(StrEnum):
    RIM = "rim"
    TIRE = "tire"


class TireConditionType(StrEnum):
    OK = "ok"
    WORN = "worn"
    UNEVEN_WEAR = "uneven_wear"
    INNER_WEAR = "inner_wear"
    OUTER_WEAR = "outer_wear"
    DAMAGED = "damaged"
    CRACKED = "cracked"
    FOREIGN_OBJECT = "foreign_object"
    LOW_TREAD = "low_tread"
    UNKNOWN = "unknown"
