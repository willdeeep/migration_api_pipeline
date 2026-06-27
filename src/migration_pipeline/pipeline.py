"""Orchestration: extract -> validate -> transform -> load.

Wires the single-purpose modules together and emits a run summary. Keeping the
orchestration here (and out of the modules) means each stage stays independently
testable and the control flow for a migration run is readable in one place.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .config import Settings, load_settings
from .logging import configure_logging

logger = logging.getLogger("migration_pipeline")


@dataclass
class RunSummary:
    """Counts emitted at the end of a run for operational visibility."""

    fetched: int = 0
    valid: int = 0
    quarantined: int = 0
    loaded: int = 0


def run(settings: Settings | None = None) -> RunSummary:
    """Execute one migration run end-to-end.

    Implemented in Phase 1: fetch -> transform -> load, returning a populated
    :class:`RunSummary`; validation/quarantine wired in Phase 2.
    """
    settings = settings or load_settings()
    configure_logging(settings.log_level)
    raise NotImplementedError("Implemented in Phase 1 (local spike).")
