# Architecture

Migration-oriented ingestion pipeline: extract university-chapter records from the
**Ducks Unlimited** ArcGIS Feature Service (the legacy source), filter to
**CA / OR / WA**, validate and transform them, and load them into **BigQuery**
(the cloud migration target). It runs daily as a Cloud Run Job on GCP.

## Data flow

```
ArcGIS Feature Service (Ducks Unlimited, FeatureServer/0/query)
        │  HTTP GET — where State IN ('CA','OR','WA'), outFields, f=geojson, paginated
        ▼
   Extract  ──►  Validate  ──►  Transform  ──►  Load  ──►  BigQuery table
  client.py     validate.py     transform.py    load.py    migration.university_chapters
        │                                          │
        │                                          └─ idempotent WRITE_TRUNCATE snapshot
        └──────────── structured JSON logging + run summary (pipeline.py) ─────────────
```

Extraction and validation/transform are separated so each is independently
testable, and the boundaries are expressed as Protocols (`FeatureSource`,
`ChapterSink`) in `pipeline.py` — this is the seam that lets tests inject fakes
and lets an alternative target (e.g. Cloud SQL Postgres) replace the BigQuery
loader without touching extract/validate/transform.

## Modules

| Module | Responsibility | Key dependencies |
|---|---|---|
| `config.py` | Runtime config from env via pydantic-settings; no secrets in code | — |
| `client.py` | ArcGIS HTTP client: server-side state filter, pagination, tenacity retries on transient/5xx | httpx, tenacity |
| `schema.py` | `ChapterRecord` (source/target contract) + `BIGQUERY_SCHEMA` | pydantic |
| `transform.py` | Field extraction, type coercion, null/blank/missing handling, coordinate parsing (pure) | schema |
| `validate.py` | Row-level validation + quarantine (with reasons); partitions valid vs quarantined | schema, transform |
| `load.py` | Ensures dataset/table; idempotent `WRITE_TRUNCATE` load; the swappable target seam | google-cloud-bigquery |
| `pipeline.py` | Orchestration over `FeatureSource`/`ChapterSink`; emits `RunSummary` | all |
| `logging.py` | Structured JSON logging; quiets noisy third-party loggers | — |
| `__main__.py` | CLI entrypoint (`python -m migration_pipeline`) | pipeline |

## Schema mapping

Source is a GeoJSON `FeatureServer` layer (point geometry, WGS84). Target field
names match `BIGQUERY_SCHEMA` exactly.

| Source (ArcGIS) | Type | Target column | BQ type | Mode |
|---|---|---|---|---|
| `ChapterID` | string | `chapter_id` | STRING | REQUIRED |
| `University_Chapter` | string | `chapter_name` | STRING | NULLABLE |
| `City` | string | `city` | STRING | NULLABLE |
| `State` | string | `state` | STRING | REQUIRED |
| `geometry.coordinates[0]` | number | `longitude` | FLOAT | NULLABLE |
| `geometry.coordinates[1]` | number | `latitude` | FLOAT | NULLABLE |

**Data shape (as of writing):** the source holds ~136 chapters across 37 states;
filtering to CA/OR/WA yields **3 records — all in California** (Oregon and
Washington currently have no chapters). The pipeline treats a *small* result as
normal; only a *zero-from-source* extract is treated as suspect (see below).

## Migration-safety behaviours

- **Schema-aware ingestion** — pydantic models define the contract; only the
  required source attributes are requested (`outFields`, never `*`).
- **Validation + quarantine** — each record is checked (id/state present, state
  in scope, coordinates in range). Failures are **quarantined** (kept with the
  raw payload + a reason and counted), never silently dropped.
- **Null / missing / type coercion** — missing optional fields → `NULL`; blanks
  normalised; coordinates coerced to float; state normalised to upper-case.
- **Idempotent load** — `WRITE_TRUNCATE` snapshot: re-running a day converges to
  the same target state. An **empty extract is a no-op** so a transient source
  outage never wipes the target.
- **Retries** — transient HTTP/5xx errors retried with exponential backoff.
- **Observability** — structured JSON logs and a per-run summary
  (`fetched / valid / quarantined / loaded`).

## GCP topology

Terraform is split into two layers ([infra/terraform](../infra/terraform)):

```
bootstrap/  (applied once, locally, with ADC — local state)
  • GCS state bucket (versioned)         • enabled APIs
  • WIF pool + provider (github-pool / github-provider)
  • tf-deployer SA (+ project roles, impersonable by this repo via WIF)

main/  (state in the GCS bucket; applied by CI)
  • Artifact Registry  (migration)                     ← images
  • BigQuery           (dataset migration, table university_chapters)
  • Cloud Run Job      (migration-job)   runs as →  migration-runtime SA
  • Secret Manager     (migration-source-url)  → injected into the job
  • Cloud Scheduler    (migration-daily, 06:00 UTC)  invokes job as →  migration-invoker SA
```

### Identity & auth (no JSON keys anywhere)

| Context | Identity | Grants |
|---|---|---|
| Local dev / Docker | Your **ADC** (`gcloud auth application-default login`) | your own permissions |
| CI/CD (GitHub Actions) | **WIF** → impersonates `tf-deployer` | deploy the `main` layer |
| Job runtime | `migration-runtime` SA | `bigquery.dataEditor` (dataset), `bigquery.jobUser`, `secretmanager.secretAccessor` |
| Scheduler → job | `migration-invoker` SA | `run.invoker` on the job |

The WIF provider is locked to this repository by an attribute condition
(`assertion.repository == "willdeeep/migration_api_pipeline"`), and the SA is
impersonable only by that repo's `principalSet`. See [cicd.md](cicd.md).

## Deployment flow

```
PR ─► CI (ruff, mypy, pytest) ─► merge to main ─► Deploy workflow:
   WIF auth → ensure Artifact Registry → build & push image (:sha, :latest)
   → terraform apply (main) → execute job (smoke test) → BigQuery
```

Daily thereafter, Cloud Scheduler triggers the same Cloud Run Job. See the
[runbook](runbook.md) for operations.

## Target-datastore deviation

The brief is internally inconsistent (Task 1 says BigQuery; the Overview and
Task 3 say Postgres). This implementation uses **BigQuery** per Task 1's literal
wording — serverless and free-tier friendly. Because `load.py` is a narrow
interface, a Cloud SQL Postgres target could be substituted without changing
extract / transform / validate.
