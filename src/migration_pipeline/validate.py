"""Row- and run-level validation with quarantine semantics.

Validation never silently drops data: a feature that fails any rule is separated
into a quarantine bucket (kept with its raw payload and a reason) so a migration
run is auditable and re-runnable. Valid features are returned as typed
:class:`ChapterRecord` instances ready to load.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from .config import TARGET_STATES
from .schema import ChapterRecord
from .transform import to_chapter_record

# Plausible geographic bounds for WGS84 coordinates.
_LON_MIN, _LON_MAX = -180.0, 180.0
_LAT_MIN, _LAT_MAX = -90.0, 90.0


@dataclass
class QuarantinedRecord:
    """A record that failed validation, kept for auditing rather than dropped."""

    raw: dict[str, Any]
    reason: str


@dataclass
class ValidationResult:
    """Outcome of validating a batch of features."""

    valid: list[ChapterRecord] = field(default_factory=list)
    quarantined: list[QuarantinedRecord] = field(default_factory=list)


def _reason_for(record: ChapterRecord) -> str | None:
    """Return a quarantine reason if ``record`` violates a rule, else ``None``."""
    if not record.chapter_id:
        return "missing chapter_id"
    if not record.state:
        return "missing state"
    if record.state not in TARGET_STATES:
        return f"state '{record.state}' not in migration scope {TARGET_STATES}"
    if record.longitude is not None and not (_LON_MIN <= record.longitude <= _LON_MAX):
        return f"longitude {record.longitude} out of range"
    if record.latitude is not None and not (_LAT_MIN <= record.latitude <= _LAT_MAX):
        return f"latitude {record.latitude} out of range"
    return None


def validate_features(features: Iterable[dict[str, Any]]) -> ValidationResult:
    """Transform and validate raw features, partitioning valid vs quarantined.

    Transformation failures and rule violations both quarantine the raw feature
    with a human-readable reason; nothing is dropped silently.
    """
    result = ValidationResult()
    for feature in features:
        try:
            record = to_chapter_record(feature)
        except Exception as exc:
            # Never let one malformed row abort the whole migration run.
            result.quarantined.append(
                QuarantinedRecord(raw=feature, reason=f"transform error: {exc}")
            )
            continue

        reason = _reason_for(record)
        if reason is None:
            result.valid.append(record)
        else:
            result.quarantined.append(QuarantinedRecord(raw=feature, reason=reason))
    return result
