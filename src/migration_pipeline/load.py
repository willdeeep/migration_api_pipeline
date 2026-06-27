"""BigQuery loader (the migration target boundary).

Owns all BigQuery interaction: ensuring the dataset/table exist with the agreed
schema and writing records idempotently so a re-run of a given day converges to
the same target state. Authentication is via Application Default Credentials
(OAuth locally, attached service account on Cloud Run) — never a JSON key.

This narrow interface is the seam at which a Cloud SQL Postgres loader could be
substituted, per the spec's documented alternative target.
"""

from __future__ import annotations

import logging
from typing import Any

from google.cloud import bigquery

from .config import Settings
from .schema import BIGQUERY_SCHEMA, ChapterRecord

logger = logging.getLogger("migration_pipeline.load")


def record_to_row(record: ChapterRecord) -> dict[str, Any]:
    """Serialize a :class:`ChapterRecord` to a BigQuery JSON row.

    Field names match :data:`BIGQUERY_SCHEMA` exactly; ``None`` is preserved so
    nullable columns load as SQL NULL.
    """
    return record.model_dump()


def _schema() -> list[bigquery.SchemaField]:
    return [
        bigquery.SchemaField(name, field_type, mode=mode)
        for name, field_type, mode in BIGQUERY_SCHEMA
    ]


class BigQueryLoader:
    """Writes validated chapter records into the BigQuery migration target."""

    def __init__(self, settings: Settings, client: bigquery.Client | None = None) -> None:
        self._settings = settings
        self._client = client or bigquery.Client(project=settings.gcp_project)

    @property
    def table_ref(self) -> str:
        s = self._settings
        return f"{s.gcp_project}.{s.bq_dataset}.{s.bq_table}"

    def ensure_target(self) -> None:
        """Create the dataset and table if absent, using the agreed schema."""
        s = self._settings
        dataset = bigquery.Dataset(f"{s.gcp_project}.{s.bq_dataset}")
        dataset.location = s.bq_location
        self._client.create_dataset(dataset, exists_ok=True)

        table = bigquery.Table(self.table_ref, schema=_schema())
        self._client.create_table(table, exists_ok=True)
        logger.info("Ensured BigQuery target", extra={"table": self.table_ref})

    def load(self, records: list[ChapterRecord]) -> int:
        """Idempotently write ``records`` (full-snapshot truncate); return row count.

        Re-running with the same input converges to the same target state. An
        empty input is a no-op (the existing snapshot is left intact) so a
        transient empty extract never wipes the target.
        """
        rows = [record_to_row(r) for r in records]
        if not rows:
            logger.warning("No records to load; leaving existing snapshot intact")
            return 0

        job_config = bigquery.LoadJobConfig(
            schema=_schema(),
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )
        job = self._client.load_table_from_json(rows, self.table_ref, job_config=job_config)
        job.result()
        logger.info("Loaded rows into BigQuery", extra={"rows": len(rows), "table": self.table_ref})
        return len(rows)

    def row_count(self) -> int:
        """Return the current row count of the target table."""
        query = f"SELECT COUNT(*) AS n FROM `{self.table_ref}`"
        result = self._client.query(query).result()
        return int(next(iter(result)).n)
