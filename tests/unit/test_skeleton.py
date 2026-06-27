"""Phase 0 smoke tests: the package wires together and contracts are coherent.

These assert structure, not behaviour. Stage logic is covered by TDD in later
phases.
"""

from __future__ import annotations

import migration_pipeline
from migration_pipeline.config import TARGET_STATES
from migration_pipeline.schema import BIGQUERY_SCHEMA, ChapterRecord


def test_package_has_version() -> None:
    assert migration_pipeline.__version__ == "0.1.0"


def test_target_states_in_scope() -> None:
    assert TARGET_STATES == ("CA", "OR", "WA")


def test_bigquery_schema_matches_record_fields() -> None:
    """The BigQuery schema and the Pydantic contract must not drift apart."""
    schema_columns = {name for name, _type, _mode in BIGQUERY_SCHEMA}
    assert schema_columns == set(ChapterRecord.model_fields)


def test_chapter_record_round_trips() -> None:
    record = ChapterRecord(
        chapter_id="123",
        chapter_name="Example State University",
        city="Sacramento",
        state="CA",
        longitude=-121.49,
        latitude=38.58,
    )
    assert record.state == "CA"
    assert record.model_dump()["chapter_id"] == "123"
