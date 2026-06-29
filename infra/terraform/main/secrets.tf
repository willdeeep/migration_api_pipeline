# Secret Manager (#8). Demonstrates runtime-config separation: the source
# endpoint (a "connection string" to the legacy system) is managed as a secret
# and injected into the job, rather than baked into the image or plain env.
resource "google_secret_manager_secret" "source_url" {
  secret_id = "migration-source-url"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "source_url" {
  secret      = google_secret_manager_secret.source_url.id
  secret_data = var.source_url
}

# Only the runtime identity may read it.
resource "google_secret_manager_secret_iam_member" "runtime_access" {
  secret_id = google_secret_manager_secret.source_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"
}
