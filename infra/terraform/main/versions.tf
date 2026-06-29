terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # State lives in the GCS bucket created by the bootstrap layer. The bucket name
  # is supplied at init time so this config stays environment-agnostic:
  #   terraform init -backend-config="bucket=<state_bucket from bootstrap>"
  backend "gcs" {
    prefix = "main"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
