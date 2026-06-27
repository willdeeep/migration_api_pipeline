# Runbook

> Placeholder — expanded in Phase 6.

## Operational notes (to be documented)

- **Manual run:** how to trigger the Cloud Run Job out of schedule.
- **Re-run / backfill:** the load is idempotent (snapshot), so re-running a day
  converges to the same target state.
- **Failure triage:** where to find structured logs (Cloud Logging), how to read
  the run summary (fetched / valid / quarantined / loaded), common failure modes.
- **Secrets:** managed in Secret Manager; rotation procedure.
- **Teardown:** `terraform destroy` to keep within free/low-cost tiers.

## Deviation note: target datastore

The brief is internally inconsistent (Task 1 says BigQuery; the Overview and
Task 3 say Postgres). This implementation uses **BigQuery** per Task 1's literal
wording — serverless and free-tier friendly. The loader (`load.py`) is a narrow
interface, so a Cloud SQL Postgres target could be substituted with no change to
extract/transform/validate.
