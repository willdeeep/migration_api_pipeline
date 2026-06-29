# Cloud Scheduler (#7): triggers the daily migration by calling the Cloud Run
# Admin API to execute the job, authenticated as the least-privilege invoker SA.
resource "google_cloud_scheduler_job" "daily" {
  name      = "migration-daily"
  region    = var.region
  schedule  = var.schedule
  time_zone = var.scheduler_timezone

  attempt_deadline = "320s"

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.migration.name}:run"

    oauth_token {
      service_account_email = google_service_account.invoker.email
    }
  }

  depends_on = [google_cloud_run_v2_job_iam_member.invoker]
}
