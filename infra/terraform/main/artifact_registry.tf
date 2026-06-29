# Docker repository the CI pipeline pushes the migration image to (#4).
resource "google_artifact_registry_repository" "migration" {
  repository_id = var.ar_repository_id
  location      = var.region
  format        = "DOCKER"
  description   = "Migration pipeline container images"
}
