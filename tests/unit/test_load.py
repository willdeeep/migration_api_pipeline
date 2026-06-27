"""Unit tests for the BigQuery loader's pure serialization seam."""

from __future__ import annotations

from migration_pipeline.load import record_to_row
from migration_pipeline.schema import BIGQUERY_SCHEMA, ChapterRecord


def test_record_serialises_to_row_with_schema_columns() -> None:
    record = ChapterRecord(
        chapter_id="CA-0355",
        chapter_name="Cal Poly",
        city="San Luis Obispo",
        state="CA",
        longitude=-120.66,
        latitude=35.27,
    )

    row = record_to_row(record)

    assert row == {
        "chapter_id": "CA-0355",
        "chapter_name": "Cal Poly",
        "city": "San Luis Obispo",
        "state": "CA",
        "longitude": -120.66,
        "latitude": 35.27,
    }
    assert set(row) == {name for name, _type, _mode in BIGQUERY_SCHEMA}


def test_nulls_are_preserved_in_row() -> None:
    record = ChapterRecord(
        chapter_id="CA-1",
        chapter_name=None,
        city=None,
        state="CA",
        longitude=None,
        latitude=None,
    )

    row = record_to_row(record)

    assert row["chapter_name"] is None
    assert row["city"] is None
    assert row["longitude"] is None
    assert row["latitude"] is None
