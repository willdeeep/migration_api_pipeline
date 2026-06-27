"""Orchestration: extract -> transform -> load.

Wires the single-purpose modules together and emits a run summary. Keeping the
orchestration here (and out of the modules) means each stage stays independently
testable and the control flow for a migration run is readable in one place.

Source and sink are expressed as Protocols so the real ArcGIS client / BigQuery
loader can be swapped for fakes in tests, and so an alternative target (e.g.
Cloud SQL Postgres) could be substituted without touching this module.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Protocol

from .config import TARGET_STATES, Settings, load_settings
from .logging import configure_logging
from .schema import ChapterRecord
from .transform import to_chapter_record

logger = logging.getLogger("migration_pipeline")


class FeatureSource(Protocol):
    """Yields raw source feature dicts for the requested states."""

    def fetch_features(self, states: tuple[str, ...]) -> Iterator[dict[str, Any]]: ...


class ChapterSink(Protocol):
    """Migration target: ensures schema exists and loads validated records."""

    def ensure_target(self) -> None: ...

    def load(self, records: list[ChapterRecord]) -> int: ...


@dataclass
class RunSummary:
    """Counts emitted at the end of a run for operational visibility."""

    fetched: int = 0
    valid: int = 0
    quarantined: int = 0
    loaded: int = 0


def run(
    settings: Settings | None = None,
    *,
    source: FeatureSource | None = None,
    sink: ChapterSink | None = None,
) -> RunSummary:
    """Execute one migration run end-to-end and return a :class:`RunSummary`.

    Validation/quarantine is wired in Phase 2; for now every transformed record
    is treated as valid.
    """
    settings = settings or load_settings()
    configure_logging(settings.log_level)

    # Imported lazily so unit tests can inject fakes without importing the BigQuery
    # / httpx-backed implementations (and their dependencies).
    if source is None:
        from .client import ArcGisClient

        source = ArcGisClient(settings)
    if sink is None:
        from .load import BigQueryLoader

        sink = BigQueryLoader(settings)

    logger.info("Starting migration run", extra={"states": list(TARGET_STATES)})
    sink.ensure_target()

    records = [to_chapter_record(feature) for feature in source.fetch_features(TARGET_STATES)]
    summary = RunSummary(fetched=len(records), valid=len(records))

    summary.loaded = sink.load(records)
    logger.info(
        "Migration run finished",
        extra={
            "fetched": summary.fetched,
            "valid": summary.valid,
            "quarantined": summary.quarantined,
            "loaded": summary.loaded,
        },
    )
    return summary
