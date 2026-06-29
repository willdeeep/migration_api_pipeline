output "artifact_registry_repo" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.migration.repository_id}"
  description = "Base path CI pushes images to."
}

output "cloud_run_job" {
  value       = google_cloud_run_v2_job.migration.name
  description = "Cloud Run Job name."
}

output "runtime_service_account" {
  value       = google_service_account.runtime.email
  description = "Job runtime identity."
}

output "bigquery_table" {
  value       = "${var.project_id}.${google_bigquery_dataset.migration.dataset_id}.${google_bigquery_table.university_chapters.table_id}"
  description = "Fully-qualified migration target table."
}
