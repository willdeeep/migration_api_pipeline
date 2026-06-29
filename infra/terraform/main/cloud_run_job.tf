# Cloud Run Job: one container invocation == one migration run (#6).
# Non-sensitive config is plain env; the source endpoint comes from Secret Manager.
resource "google_cloud_run_v2_job" "migration" {
  name                = "migration-job"
  location            = var.region
  deletion_protection = false

  template {
    template {
      service_account = google_service_account.runtime.email
      max_retries     = 1
      timeout         = "900s"

      containers {
        image = var.image

        env {
          name  = "MIGRATION_GCP_PROJECT"
          value = var.project_id
        }
        env {
          name  = "MIGRATION_BQ_DATASET"
          value = var.bq_dataset
        }
        env {
          name  = "MIGRATION_BQ_TABLE"
          value = var.bq_table
        }
        env {
          name  = "MIGRATION_BQ_LOCATION"
          value = var.bq_location
        }
        env {
          name  = "MIGRATION_LOG_LEVEL"
          value = var.log_level
        }
        env {
          name = "MIGRATION_SOURCE_URL"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.source_url.secret_id
              version = "latest"
            }
          }
        }
      }
    }
  }

  # The secret version and the runtime's accessor binding must exist first.
  depends_on = [
    google_secret_manager_secret_version.source_url,
    google_secret_manager_secret_iam_member.runtime_access,
  ]
}
