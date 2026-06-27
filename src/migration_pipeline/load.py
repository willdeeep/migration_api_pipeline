"""BigQuery loader (the migration target boundary).

Owns all BigQuery interaction: ensuring the dataset/table exist with the agreed
schema and writing records idempotently so a re-run of a given day converges to
the same target state. Authentication is via Application Default Credentials
(OAuth locally, attached service account on Cloud Run) — never a JSON key.

This narrow interface is the seam at which a Cloud SQL Postgres loader could be
substituted, per the spec's documented alternative target.
"""

from __future__ import annotations

from .config import Settings
from .schema import ChapterRecord


class BigQueryLoader:
    """Writes validated chapter records into the BigQuery migration target."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def ensure_target(self) -> None:
        """Create the dataset/table if absent, using ``schema.BIGQUERY_SCHEMA``."""
        raise NotImplementedError("Implemented in Phase 1 (local spike).")

    def load(self, records: list[ChapterRecord]) -> int:
        """Idempotently write ``records``; return the number of rows loaded.

        Implemented in Phase 1 (WRITE_TRUNCATE snapshot), hardened to MERGE in
        Phase 2 if incremental semantics are required.
        """
        raise NotImplementedError("Implemented in Phase 1 (local spike).")
