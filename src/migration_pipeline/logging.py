"""Structured (JSON) logging setup for repeatable migration runs.

A single ``configure_logging`` call wires the root logger to emit one JSON
object per line, which is friendly to Cloud Logging and to local ``jq``.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any


class JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # Include any structured extras attached via ``logger.info(..., extra=...)``.
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value
        return json.dumps(payload, default=str)


_RESERVED = frozenset(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging to emit JSON lines at ``level``."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
