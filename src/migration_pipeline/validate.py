"""Row- and run-level validation with quarantine semantics.

Validation never silently drops data: invalid rows are separated into a
quarantine bucket (logged and counted) so a migration run is auditable and
re-runnable. Run-level assertions guard against obviously broken extracts
(e.g. zero rows returned).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schema import ChapterRecord


@dataclass
class QuarantinedRecord:
    """A record that failed validation, kept for auditing rather than dropped."""

    raw: dict[str, Any]
    reason: str


@dataclass
class ValidationResult:
    """Outcome of validating a batch of records."""

    valid: list[ChapterRecord] = field(default_factory=list)
    quarantined: list[QuarantinedRecord] = field(default_factory=list)


def validate_records(
    records: list[ChapterRecord],
    raw_by_index: list[dict[str, Any]],
) -> ValidationResult:
    """Partition records into valid and quarantined.

    Implemented in Phase 2: enforce state in scope, coordinate ranges, required
    fields; everything else is quarantined with a reason.
    """
    raise NotImplementedError("Implemented in Phase 2 (hardening).")
