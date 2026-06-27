"""Integration test: BigQueryLoader against a real (temporary) BigQuery table.

Requires Application Default Credentials and a GCP project. Skipped when
credentials or project are unavailable (e.g. in CI without WIF), so the unit
suite remains runnable everywhere.

Run explicitly with:  uv run pytest -m integration
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import pytest

pytestmark = pytest.mark.integration

google_auth = pytest.importorskip("google.auth")
bigquery = pytest.importorskip("google.cloud.bigquery")

from migration_pipeline.config import Settings  # noqa: E402
from migration_pipeline.load import BigQueryLoader  # noqa: E402
from migration_pipeline.schema import ChapterRecord  # noqa: E402


def _project() -> str:
    try:
        _creds, project = google_auth.default()
    except Exception:  # pragma: no cover - environment dependent
        pytest.skip("No Application Default Credentials available")
    project = os.environ.get("MIGRATION_GCP_PROJECT") or project
    if not project:
        pytest.skip("No GCP project resolved")
    return str(project)


@pytest.fixture
def loader() -> Iterator[BigQueryLoader]:
    project = _project()
    dataset = f"migration_it_{uuid.uuid4().hex[:8]}"
    settings = Settings(
        source_url="https://example.test/query",
        gcp_project=project,
        bq_dataset=dataset,
        bq_table="university_chapters",
    )
    client = bigquery.Client(project=project)
    yield BigQueryLoader(settings, client=client)
    client.delete_dataset(dataset, delete_contents=True, not_found_ok=True)


def test_ensure_target_and_idempotent_load(loader: BigQueryLoader) -> None:
    records = [
        ChapterRecord(
            chapter_id="CA-1",
            chapter_name="Cal Poly",
            city="San Luis Obispo",
            state="CA",
            longitude=-120.66,
            latitude=35.27,
        ),
        ChapterRecord(
            chapter_id="CA-2",
            chapter_name=None,
            city=None,
            state="CA",
            longitude=None,
            latitude=None,
        ),
    ]

    loader.ensure_target()
    loaded = loader.load(records)
    assert loaded == 2

    # Re-running truncates and reloads: count stays 2 (idempotent snapshot).
    loader.load(records)
    count = loader.row_count()
    assert count == 2
