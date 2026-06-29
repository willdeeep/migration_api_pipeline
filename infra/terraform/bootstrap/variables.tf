variable "project_id" {
  type        = string
  description = "GCP project ID hosting the migration pipeline."
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "Default region for regional resources."
}

variable "state_bucket_name" {
  type        = string
  description = "Globally-unique GCS bucket name for the main layer's Terraform state."
}

variable "github_repository" {
  type        = string
  description = "GitHub repo (owner/name) allowed to authenticate via WIF, e.g. willdeeep/migration_api_pipeline."
}
