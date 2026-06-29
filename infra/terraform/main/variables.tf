variable "project_id" {
  type        = string
  description = "GCP project ID."
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "Region for Artifact Registry, Cloud Run, and Cloud Scheduler."
}

variable "image" {
  type        = string
  description = "Full container image reference (incl. tag) for the Cloud Run Job. Supplied by CI per build."
}

variable "ar_repository_id" {
  type        = string
  default     = "migration"
  description = "Artifact Registry Docker repository ID."
}

variable "bq_dataset" {
  type        = string
  default     = "migration"
  description = "BigQuery dataset ID (migration target)."
}

variable "bq_table" {
  type        = string
  default     = "university_chapters"
  description = "BigQuery table ID."
}

variable "bq_location" {
  type        = string
  default     = "US"
  description = "BigQuery dataset location (multi-region)."
}

variable "source_url" {
  type        = string
  description = "ArcGIS FeatureServer query endpoint; stored in Secret Manager and injected into the job."
}

variable "schedule" {
  type        = string
  default     = "0 6 * * *"
  description = "Cron schedule for the daily migration run."
}

variable "scheduler_timezone" {
  type        = string
  default     = "Etc/UTC"
  description = "Time zone for the Cloud Scheduler job."
}

variable "log_level" {
  type        = string
  default     = "INFO"
  description = "Application log level."
}
