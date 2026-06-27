"""ArcGIS Feature Service HTTP client.

Responsible only for talking to the source system: builds paginated queries,
applies retries/backoff on transient failures, and yields raw feature dicts.
Filtering/transformation live elsewhere so this stays a thin I/O boundary.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .config import Settings


class ArcGisClient:
    """Fetches raw features from the ArcGIS FeatureServer query endpoint."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def fetch_features(self, states: tuple[str, ...]) -> Iterator[dict[str, Any]]:
        """Yield raw ArcGIS feature dicts for the given states.

        Implemented in Phase 1: server-side ``where state IN (...)`` filter with
        ``resultOffset``/``resultRecordCount`` pagination and tenacity retries.
        """
        raise NotImplementedError("Implemented in Phase 1 (local spike).")
