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

# Third-party loggers turned down so migration run logs stay readable. httpx logs
# every request at INFO (our client already logs each page); google.auth emits a
# benign "no project" warning even though we pass the project explicitly.
_THIRD_PARTY_LEVELS = {
    "httpx": logging.WARNING,
    "httpcore": logging.WARNING,
    "google.auth": logging.ERROR,
    "google.auth._default": logging.ERROR,
}


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging to emit JSON lines at ``level``."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    for name, third_party_level in _THIRD_PARTY_LEVELS.items():
        logging.getLogger(name).setLevel(third_party_level)
