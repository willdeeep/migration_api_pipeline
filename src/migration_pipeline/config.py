"""Runtime configuration loaded from the environment.

Single source of truth for runtime config. No secrets are hard-coded; values
come from environment variables (locally via ``.env``, in the cloud via the
Cloud Run Job environment / Secret Manager). See ``.env.example``.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# States in scope for the migration (Task 1: filter to CA, OR, WA).
TARGET_STATES: tuple[str, ...] = ("CA", "OR", "WA")


class Settings(BaseSettings):
    """Pipeline runtime configuration.

    Populated from environment variables prefixed with ``MIGRATION_``.
    """

    model_config = SettingsConfigDict(
        env_prefix="MIGRATION_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Source (ArcGIS Feature Service) ---
    source_url: str = Field(
        description="ArcGIS FeatureServer query endpoint for DU University Chapters.",
    )
    source_page_size: int = Field(
        default=1000,
        description="Records per page when paginating the source API.",
    )
    request_timeout_seconds: float = Field(default=30.0)
    max_retries: int = Field(default=5)

    # --- Target (BigQuery) ---
    gcp_project: str = Field(description="GCP project hosting the BigQuery target.")
    bq_dataset: str = Field(default="migration", description="BigQuery dataset id.")
    bq_table: str = Field(default="university_chapters", description="BigQuery table id.")
    bq_location: str = Field(default="US", description="BigQuery dataset location.")

    # --- Observability ---
    log_level: str = Field(default="INFO")


def load_settings() -> Settings:
    """Construct :class:`Settings` from the environment."""
    return Settings()  # type: ignore[call-arg]
