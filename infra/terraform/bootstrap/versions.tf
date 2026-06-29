terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # Bootstrap uses LOCAL state on purpose: it creates the GCS bucket that the
  # main layer then uses as its backend (chicken-and-egg). Commit this state's
  # config but not the state file itself.
}

provider "google" {
  project = var.project_id
  region  = var.region
}
