# Migration API Pipeline

A migration-oriented data ingestion pipeline that extracts university chapter
records from the **Ducks Unlimited** ArcGIS Feature Service (the legacy source
system), filters to **California, Oregon, and Washington**, validates and
transforms them, and loads them into **BigQuery** (the cloud migration target).

It is containerised, deployed to GCP as a scheduled daily **Cloud Run Job**, and
built/shipped via **GitHub Actions** with keyless authentication.

> Status: **Deployed and running on GCP.** The pipeline runs end-to-end locally,
> in a container, and in the cloud as a scheduled Cloud Run Job — built and
> shipped by CI/CD with keyless auth. See [docs/architecture.md](docs/architecture.md)
> and the [runbook](docs/runbook.md).

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

Containerised run — a teammate can run the whole migration with one command.
Prerequisites: a `.env` (see `.env.example`) and local ADC
(`gcloud auth application-default login`); compose mounts your ADC read-only so
the container authenticates exactly as you do locally.

```bash
docker compose run --rm migration
```

The image is multi-stage (built with the `uv` base image, shipped on
`python:3.14-slim`), runs as a non-root user, and is ~210 MB.

## Deployment

Provisioned by **Terraform** ([infra/terraform](infra/terraform)) and shipped by
**GitHub Actions**, all with keyless auth (Workload Identity Federation — no JSON
keys):

```
PR ─► CI (ruff · mypy · pytest) ─► merge to main ─► Deploy:
   build & push image → terraform apply → Cloud Run Job → daily via Cloud Scheduler → BigQuery
```

Infra is two Terraform layers — `bootstrap/` (WIF, deployer SA, state bucket;
applied once locally) and `main/` (Artifact Registry, BigQuery, Cloud Run Job,
Scheduler, Secret Manager). See [docs/cicd.md](docs/cicd.md) for the pipeline and
enablement, and the [runbook](docs/runbook.md) for operations.

## Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md) — branch flow, PR gate, pre-commit
- [docs/cicd.md](docs/cicd.md) — CI/CD pipeline and enablement
- [docs/architecture.md](docs/architecture.md) — system design
- [docs/runbook.md](docs/runbook.md) — operational notes, re-runs, teardown

## Contributing

`main` is protected — changes land via pull request and must pass CI. See
[CONTRIBUTING.md](CONTRIBUTING.md).

## Roadmap

- ✅ **Phase 0** — Skeleton & tooling
- ✅ **Phase 1** — Local functional spike (end-to-end: API → BigQuery)
- ✅ **Phase 2** — Production hardening (validation/quarantine, retries, idempotency)
- ✅ **Phase 3** — Containerisation (Dockerfile, docker-compose)
- ✅ **Phase 4** — Infrastructure as Code (Terraform on GCP)
- ✅ **Phase 5** — CI/CD (GitHub Actions, keyless WIF)
- ✅ **Phase 6** — Docs & operational readiness
