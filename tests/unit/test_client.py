"""Tests for the ArcGIS Feature Service client (pagination, filtering, retries)."""

from __future__ import annotations

from typing import Any

import httpx
import respx

from migration_pipeline.client import ArcGisClient
from migration_pipeline.config import Settings

BASE = "https://example.test/FeatureServer/0/query"


def _settings(**overrides: Any) -> Settings:
    base: dict[str, Any] = {
        "source_url": BASE,
        "gcp_project": "test-project",
        "source_page_size": 2,
        "max_retries": 3,
    }
    base.update(overrides)
    return Settings(**base)


def _page(*chapter_ids: str, exceeded: bool = False) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "properties": {"exceededTransferLimit": exceeded},
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-120.0, 35.0]},
                "properties": {"ChapterID": cid, "State": "CA"},
            }
            for cid in chapter_ids
        ],
    }


@respx.mock
def test_returns_all_features_from_a_single_page() -> None:
    respx.get(url__startswith=BASE).mock(
        return_value=httpx.Response(200, json=_page("CA-1", "CA-2", exceeded=False))
    )

    features = list(ArcGisClient(_settings()).fetch_features(("CA", "OR", "WA")))

    assert [f["properties"]["ChapterID"] for f in features] == ["CA-1", "CA-2"]


@respx.mock
def test_paginates_until_transfer_limit_not_exceeded() -> None:
    route = respx.get(url__startswith=BASE).mock(
        side_effect=[
            httpx.Response(200, json=_page("CA-1", "CA-2", exceeded=True)),
            httpx.Response(200, json=_page("CA-3", exceeded=False)),
        ]
    )

    features = list(ArcGisClient(_settings()).fetch_features(("CA",)))

    assert [f["properties"]["ChapterID"] for f in features] == ["CA-1", "CA-2", "CA-3"]
    assert route.call_count == 2
    # Second request advances the offset by one page.
    assert "resultOffset=2" in str(route.calls[1].request.url)


@respx.mock
def test_sends_state_filter_in_where_clause() -> None:
    respx.get(url__startswith=BASE).mock(
        return_value=httpx.Response(200, json=_page(exceeded=False))
    )

    list(ArcGisClient(_settings()).fetch_features(("CA", "OR", "WA")))

    request_url = str(respx.calls[0].request.url)
    assert "CA" in request_url and "OR" in request_url and "WA" in request_url
    assert "State" in request_url


@respx.mock
def test_retries_transient_server_errors_then_succeeds() -> None:
    route = respx.get(url__startswith=BASE).mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(200, json=_page("CA-1", exceeded=False)),
        ]
    )

    features = list(ArcGisClient(_settings()).fetch_features(("CA",)))

    assert [f["properties"]["ChapterID"] for f in features] == ["CA-1"]
    assert route.call_count == 2
