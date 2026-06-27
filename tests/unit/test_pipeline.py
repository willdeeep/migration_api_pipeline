"""Tests for pipeline orchestration with injected source/sink fakes."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from migration_pipeline.config import Settings
from migration_pipeline.pipeline import run
from migration_pipeline.schema import ChapterRecord


def _feature(chapter_id: str, state: str = "CA") -> dict[str, Any]:
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-120.0, 35.0]},
        "properties": {
            "ChapterID": chapter_id,
            "University_Chapter": "Test University",
            "City": "Testville",
            "State": state,
        },
    }


class FakeSource:
    def __init__(self, features: list[dict[str, Any]]) -> None:
        self._features = features
        self.requested_states: tuple[str, ...] | None = None

    def fetch_features(self, states: tuple[str, ...]) -> Iterator[dict[str, Any]]:
        self.requested_states = states
        return iter(self._features)


class FakeSink:
    def __init__(self) -> None:
        self.ensured = False
        self.records: list[ChapterRecord] | None = None

    def ensure_target(self) -> None:
        self.ensured = True

    def load(self, records: list[ChapterRecord]) -> int:
        self.records = records
        return len(records)


def _settings() -> Settings:
    return Settings(source_url="https://example.test/query", gcp_project="test-project")


def test_run_extracts_transforms_and_loads() -> None:
    source = FakeSource([_feature("CA-1"), _feature("CA-2")])
    sink = FakeSink()

    summary = run(_settings(), source=source, sink=sink)

    assert sink.ensured is True
    assert summary.fetched == 2
    assert summary.valid == 2
    assert summary.loaded == 2
    assert sink.records is not None
    assert [r.chapter_id for r in sink.records] == ["CA-1", "CA-2"]


def test_run_filters_to_target_states() -> None:
    source = FakeSource([])
    run(_settings(), source=source, sink=FakeSink())

    assert source.requested_states == ("CA", "OR", "WA")


def test_run_handles_empty_source_without_error() -> None:
    summary = run(_settings(), source=FakeSource([]), sink=FakeSink())

    assert summary.fetched == 0
    assert summary.loaded == 0
