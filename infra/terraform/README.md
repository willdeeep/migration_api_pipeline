# Infrastructure (Terraform) — placeholder

Implemented in **Phase 4**. Will provision on GCP:

- **Artifact Registry** — Docker repository for the migration image
- **BigQuery** — dataset + table (schema from `migration_pipeline.schema`)
- **Cloud Run Job** — the migration job, with an attached runtime service account
- **Cloud Scheduler** — daily trigger for the job
- **Secret Manager** — runtime secrets/config
- **Workload Identity Federation** — keyless auth for GitHub Actions (Phase 5)

Authentication uses OAuth/short-lived credentials only — no JSON service-account
keys are created or stored.
