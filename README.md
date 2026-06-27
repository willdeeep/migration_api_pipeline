# Migration API Pipeline

A migration-oriented data ingestion pipeline that extracts university chapter
records from the **Ducks Unlimited** ArcGIS Feature Service (the legacy source
system), filters to **California, Oregon, and Washington**, validates and
transforms them, and loads them into **BigQuery** (the cloud migration target).

It is containerised, deployed to GCP as a scheduled daily **Cloud Run Job**, and
built/shipped via **GitHub Actions** with keyless authentication.

> Status: **Phase 0 — skeleton.** Module boundaries and tooling are in place;
> stage logic is implemented in subsequent phases (see the roadmap below).

## Architecture

```
ArcGIS Feature Service (Ducks Unlimited)
        │  HTTP GET (where state IN ('CA','OR','WA'), outFields, f=geojson, paginated)
        ▼
  Extract ──► Validate ──► Transform ──► Load ──► BigQuery table
   client.py   validate.py  transform.py  load.py
        │
        └─ structured JSON logging + run summary (pipeline.py)
```

| Module | Responsibility |
|---|---|
| `config.py` | Runtime config from env (pydantic-settings); no secrets in code |
| `client.py` | ArcGIS HTTP client: pagination, retries/backoff |
| `schema.py` | Pydantic source/target contract + BigQuery schema |
| `transform.py` | Field extraction, type coercion, null/missing handling |
| `validate.py` | Row-level validation + quarantine; run-level assertions |
| `load.py` | Idempotent BigQuery load (swappable target seam) |
| `pipeline.py` | Orchestration + run summary |
| `__main__.py` | CLI entrypoint (`python -m migration_pipeline`) |

## Tech stack

- **Python 3.14**, managed with [`uv`](https://docs.astral.sh/uv/)
- **httpx** + **tenacity** (source I/O), **pydantic** (schema), **google-cloud-bigquery** (target)
- **Docker** + **docker-compose** for local runs
- **Terraform** for GCP infra (Artifact Registry, BigQuery, Cloud Run Job, Cloud Scheduler)
- **GitHub Actions** CI/CD with Workload Identity Federation (no JSON keys)

## Setup

```bash
# 1. Install dependencies into a managed venv (Python 3.14 auto-provisioned by uv)
uv sync

# 2. Configure runtime
cp .env.example .env   # then edit values

# 3. Authenticate to GCP (OAuth — no JSON key)
gcloud auth application-default login
```

## Usage

```bash
# Run the migration locally
uv run python -m migration_pipeline

# Lint, type-check, test
uv run ruff check .
uv run mypy
uv run pytest
```

Containerised run (Phase 3):

```bash
docker compose run --rm migration
```

## Documentation

- [docs/architecture.md](docs/architecture.md) — system design
- [docs/runbook.md](docs/runbook.md) — operational notes, re-runs, teardown

## Roadmap

- **Phase 0** — Skeleton & tooling *(current)*
- **Phase 1** — Local functional spike (end-to-end: API → BigQuery)
- **Phase 2** — Production hardening (validation/quarantine, retries, idempotency)
- **Phase 3** — Containerisation (Dockerfile, docker-compose)
- **Phase 4** — Infrastructure as Code (Terraform on GCP)
- **Phase 5** — CI/CD (GitHub Actions, keyless WIF)
- **Phase 6** — Docs & operational readiness
