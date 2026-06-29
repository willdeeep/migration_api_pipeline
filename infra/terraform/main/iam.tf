# Least-privilege identities (#6).
# - runtime: the Cloud Run Job's identity — writes to the dataset, runs BQ jobs,
#   reads the source-URL secret.
# - invoker: Cloud Scheduler's identity — only allowed to run the job.

resource "google_service_account" "runtime" {
  account_id   = "migration-runtime"
  display_name = "Migration job runtime identity"
}

resource "google_service_account" "invoker" {
  account_id   = "migration-invoker"
  display_name = "Cloud Scheduler invoker for the migration job"
}

# Runtime may write data into the target dataset...
resource "google_bigquery_dataset_iam_member" "runtime_editor" {
  dataset_id = google_bigquery_dataset.migration.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.runtime.email}"
}

# ...and run load/query jobs in the project.
resource "google_project_iam_member" "runtime_jobuser" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

# Invoker may execute this specific Cloud Run Job (used by Cloud Scheduler).
resource "google_cloud_run_v2_job_iam_member" "invoker" {
  name     = google_cloud_run_v2_job.migration.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.invoker.email}"
}
