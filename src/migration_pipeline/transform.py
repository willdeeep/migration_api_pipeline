"""Pure transformation functions: raw ArcGIS feature -> ChapterRecord.

Handles the migration-safety concerns of mapping a messy legacy record into the
target contract: field extraction, type coercion, null/missing handling, and
coordinate extraction from the feature geometry. No I/O here so it is trivially
unit-testable.
"""

from __future__ import annotations

from typing import Any

from .schema import ChapterRecord


def to_chapter_record(feature: dict[str, Any]) -> ChapterRecord:
    """Map a single raw ArcGIS feature to a :class:`ChapterRecord`.

    Implemented in Phase 1: read ``attributes``/``geometry``, coerce types,
    coalesce missing optional fields to ``None``.
    """
    raise NotImplementedError("Implemented in Phase 1 (local spike).")
