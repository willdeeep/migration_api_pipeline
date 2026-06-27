"""Pure transformation functions: raw ArcGIS feature -> ChapterRecord.

Handles the migration-safety concerns of mapping a messy legacy record into the
target contract: field extraction, type coercion, null/missing handling, and
coordinate extraction from the feature geometry. No I/O here so it is trivially
unit-testable.
"""

from __future__ import annotations

from typing import Any

from .schema import ChapterRecord


def _clean_str(value: Any) -> str | None:
    """Coerce to a trimmed string, mapping empty/blank/missing to ``None``."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _to_float(value: Any) -> float | None:
    """Coerce a coordinate to ``float``; missing/invalid becomes ``None``."""
    if value is None:
        return None
    try:
        return float(value)
    except TypeError, ValueError:
        return None


def to_chapter_record(feature: dict[str, Any]) -> ChapterRecord:
    """Map a single raw ArcGIS GeoJSON feature to a :class:`ChapterRecord`.

    Tolerates missing geometry and missing/blank optional attributes (coalesced
    to ``None``). Coordinates are read as ``[longitude, latitude]`` per GeoJSON.
    """
    properties = feature.get("properties") or {}
    geometry = feature.get("geometry") or {}
    coordinates = geometry.get("coordinates") or [None, None]

    state = _clean_str(properties.get("State"))

    return ChapterRecord(
        chapter_id=_clean_str(properties.get("ChapterID")) or "",
        chapter_name=_clean_str(properties.get("University_Chapter")),
        city=_clean_str(properties.get("City")),
        state=state.upper() if state else "",
        longitude=_to_float(coordinates[0]),
        latitude=_to_float(coordinates[1]),
    )
