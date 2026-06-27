"""ArcGIS Feature Service HTTP client.

Responsible only for talking to the source system: builds paginated queries,
applies retries/backoff on transient failures, and yields raw feature dicts.
Filtering/transformation live elsewhere so this stays a thin I/O boundary.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import Settings

logger = logging.getLogger("migration_pipeline.client")

# Source attributes we request explicitly (schema-aware: we never rely on "*").
_OUT_FIELDS = "ChapterID,University_Chapter,City,State"


class TransientSourceError(Exception):
    """A retryable upstream failure (timeout, connection error, or 5xx)."""


class ArcGisClient:
    """Fetches raw features from the ArcGIS FeatureServer query endpoint."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def fetch_features(self, states: tuple[str, ...]) -> Iterator[dict[str, Any]]:
        """Yield raw ArcGIS GeoJSON feature dicts for the given states.

        Applies a server-side ``State IN (...)`` filter and paginates with
        ``resultOffset``/``resultRecordCount`` until the service reports no more
        records. Each page request is retried on transient failures.
        """
        page_size = self._settings.source_page_size
        with httpx.Client(timeout=self._settings.request_timeout_seconds) as client:
            offset = 0
            while True:
                payload = self._get_page(client, states, offset, page_size)
                features = payload.get("features") or []
                yield from features

                exceeded = bool(payload.get("properties", {}).get("exceededTransferLimit"))
                if not exceeded or len(features) < page_size:
                    break
                offset += page_size

    def _get_page(
        self,
        client: httpx.Client,
        states: tuple[str, ...],
        offset: int,
        page_size: int,
    ) -> dict[str, Any]:
        state_list = ",".join(f"'{s}'" for s in states)
        params: dict[str, str | int] = {
            "where": f"State IN ({state_list})",
            "outFields": _OUT_FIELDS,
            "returnGeometry": "true",
            "outSR": "4326",
            "orderByFields": "OBJECTID",
            "resultOffset": offset,
            "resultRecordCount": page_size,
            "f": "geojson",
        }

        @retry(
            retry=retry_if_exception_type(TransientSourceError),
            stop=stop_after_attempt(self._settings.max_retries),
            wait=wait_exponential(multiplier=0.5, max=10),
            reraise=True,
        )
        def _request() -> dict[str, Any]:
            try:
                response = client.get(self._settings.source_url, params=params)
            except httpx.TransportError as exc:
                raise TransientSourceError(str(exc)) from exc
            if response.status_code >= 500:
                raise TransientSourceError(f"upstream {response.status_code}")
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            if "error" in data:
                raise RuntimeError(f"ArcGIS error response: {data['error']}")
            return data

        logger.info("Fetching source page", extra={"offset": offset, "page_size": page_size})
        return _request()
