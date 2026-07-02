# Runbook

Operational guide for the migration pipeline. Assumes GCP project
`migration-api-pipeline`, region `us-central1`, target
`migration-api-pipeline.migration.university_chapters`.

## Prerequisites

- `gcloud` authenticated (`gcloud auth login`) and project set
  (`gcloud config set project migration-api-pipeline`).
- For local/container runs: `gcloud auth application-default login` (ADC).

## Running the migration

### Locally
```bash
uv run python -m migration_pipeline
```

### In Docker (as a teammate would)
```bash
docker compose run --rm migration
```

### In the cloud (manual, out of schedule)
```bash
gcloud run jobs execute migration-job --region us-central1 --wait
```

### Via the schedule
Cloud Scheduler runs `migration-daily` at **06:00 UTC** daily. Trigger it by hand:
```bash
gcloud scheduler jobs run migration-daily --location us-central1
```

## Re-run / backfill

The load is an **idempotent full snapshot** (`WRITE_TRUNCATE`): re-running simply
re-fetches the current source and replaces the table contents. There is no
partial state to reconcile — just execute the job again (any method above).

Because the source is a live "current chapters" dataset, there is no historical
backfill dimension; each run reflects the source as-of that moment.

## Monitoring & verification

Confirm the target after a run:
```bash
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) AS rows FROM `migration-api-pipeline.migration.university_chapters`'
```

Read the structured run summary / logs (Cloud Logging):
```bash
gcloud logging read \
  'resource.type=cloud_run_job AND resource.labels.job_name=migration-job' \
  --limit 50 --freshness 1d --format='value(timestamp, jsonPayload.message)'
```
Each run ends with a summary line carrying `fetched / valid / quarantined /
loaded`. Inspect a specific execution:
```bash
gcloud run jobs executions list --job migration-job --region us-central1 --limit 5
gcloud run jobs executions describe <EXECUTION_ID> --region us-central1
```

## Failure triage

| Symptom | Likely cause | Action |
|---|---|---|
| Job/exec fails immediately, "API … not enabled" | Service Usage propagation on a fresh project | Enable the named API (`gcloud services enable <api>`); it's a one-time settle |
| `403` on BigQuery | Runtime SA missing a grant | Confirm `migration-runtime` has `bigquery.dataEditor` on the dataset + `bigquery.jobUser` |
| `quarantined` count spikes | Source schema drift / bad rows | Inspect the `Quarantined record` log lines (reason + chapter id); adjust `validate.py`/`transform.py` |
| `fetched = 0` (warning, no load) | Source down or contract change | Target is intentionally left intact; investigate the source endpoint before forcing a run |
| Deploy fails at auth step | WIF vars unset/incorrect | Check repo Variables `WIF_PROVIDER` / `DEPLOYER_SA` (see [cicd.md](cicd.md)) |
| `terraform apply` "Already Exists" | Resource created outside Terraform | Import it (`terraform import …`) or remove the stray resource |

Quarantined records are **logged, not dropped** — a bad row never fails the whole
run, and every rejection is auditable by its reason.

## Secrets

The source endpoint is stored in **Secret Manager** (`migration-source-url`) and
injected into the job as `MIGRATION_SOURCE_URL`. To rotate/update it:
```bash
echo -n 'https://new-endpoint/query' | \
  gcloud secrets versions add migration-source-url --data-file=-
```
The job reads version `latest`, so the next execution picks it up — no redeploy
needed. (Managed in Terraform via `infra/terraform/main/secrets.tf`.)

## Deploys & rollback

- **Deploy:** merging a PR to `main` runs the Deploy workflow (build → push →
  `terraform apply` → smoke test). Images are tagged with the commit SHA.
- **Rollback:** redeploy a previous image by pointing the job at an earlier SHA
  tag —
  ```bash
  terraform -chdir=infra/terraform/main apply \
    -var image=us-central1-docker.pkg.dev/migration-api-pipeline/migration/migration-pipeline:<GOOD_SHA>
  ```
  or `gcloud run jobs update migration-job --image <…>:<GOOD_SHA> --region us-central1`.

## Teardown (stay within free/low-cost tiers)

```bash
# 1. Application infra
terraform -chdir=infra/terraform/main destroy

# 2. If the BigQuery dataset was created outside TF at some point, remove it
bq rm -r -f -d migration-api-pipeline:migration

# 3. Bootstrap (leaves APIs enabled; disable_on_destroy=false)
terraform -chdir=infra/terraform/bootstrap destroy
```
Everything here is free-tier / pennies (Cloud Run scales to zero, BigQuery data
is tiny, Scheduler is within free quota), but destroy when idle to be safe.

## Known gotchas

- **Cloud Scheduler API:** on a brand-new project the first enablement can need a
  one-time manual enable in the console (Service Usage propagation). Once enabled
  it stays enabled; Terraform reconciles idempotently.
- **Docs-only merges redeploy:** the Deploy workflow triggers on any push to
  `main`, so even a docs PR triggers a (harmless, idempotent) redeploy. Add a
  `paths-ignore` filter to `deploy.yml` if you want to avoid this.
