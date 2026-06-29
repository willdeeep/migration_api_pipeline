# GCS bucket holding the main layer's Terraform state (versioned + locked).
resource "google_storage_bucket" "tf_state" {
  name     = var.state_bucket_name
  location = "US"

  uniform_bucket_level_access = true
  force_destroy               = false

  versioning {
    enabled = true
  }

  depends_on = [google_project_service.enabled]
}
