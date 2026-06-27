"""CLI entrypoint — the container's command (`python -m migration_pipeline`)."""

from __future__ import annotations

import logging
import sys

from .pipeline import run

logger = logging.getLogger("migration_pipeline")


def main() -> int:
    """Run one migration and return a process exit code."""
    try:
        summary = run()
    except Exception:
        logger.exception("Migration run failed")
        return 1
    logger.info(
        "Migration run complete",
        extra={
            "fetched": summary.fetched,
            "valid": summary.valid,
            "quarantined": summary.quarantined,
            "loaded": summary.loaded,
        },
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
