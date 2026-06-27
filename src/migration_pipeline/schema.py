"""Schema-aware contracts for source and target records.

These Pydantic models define the migration contract: what we accept from the
legacy source and what we guarantee to the target. The concrete source field
names are confirmed in Phase 1.1 against the live ArcGIS service; the model
below is intentionally tolerant of extra/unknown source attributes.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ChapterRecord(BaseModel):
    """A validated, target-shaped university chapter row.

    This is the canonical record loaded into BigQuery. Coordinates are stored
    as separate numeric columns for query-friendliness; ``state`` is constrained
    to the in-scope set by :mod:`migration_pipeline.validate`.
    """

    model_config = ConfigDict(extra="forbid")

    chapter_id: str
    chapter_name: str | None
    city: str | None
    state: str
    longitude: float | None
    latitude: float | None


# BigQuery table schema mirrors ChapterRecord. Kept here so the loader and the
# IaC table definition share a single source of truth (Phase 1/Phase 4).
BIGQUERY_SCHEMA: tuple[tuple[str, str, str], ...] = (
    ("chapter_id", "STRING", "REQUIRED"),
    ("chapter_name", "STRING", "NULLABLE"),
    ("city", "STRING", "NULLABLE"),
    ("state", "STRING", "REQUIRED"),
    ("longitude", "FLOAT", "NULLABLE"),
    ("latitude", "FLOAT", "NULLABLE"),
)
