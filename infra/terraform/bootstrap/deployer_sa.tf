# Service account that GitHub Actions impersonates (via WIF) to deploy the main
# layer. Broad-ish project roles because it manages most of the infra; scope is
# acceptable for a single-purpose deployer and tracked as future hardening.

resource "google_service_account" "deployer" {
  account_id   = "tf-deployer"
  display_name = "Terraform deployer (GitHub Actions)"

  depends_on = [google_project_service.enabled]
}

locals {
  deployer_roles = [
    "roles/run.admin",
    "roles/artifactregistry.admin",
    "roles/bigquery.admin",
    "roles/cloudscheduler.admin",
    "roles/secretmanager.admin",
    "roles/iam.serviceAccountAdmin",
    "roles/iam.serviceAccountUser",
    "roles/storage.admin",                   # read/write Terraform state bucket
    "roles/resourcemanager.projectIamAdmin", # manage IAM bindings in the main layer
    "roles/serviceusage.serviceUsageAdmin",
  ]
}

resource "google_project_iam_member" "deployer" {
  for_each = toset(local.deployer_roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.deployer.email}"
}

# Allow GitHub Actions runs from our repo to impersonate the deployer SA.
resource "google_service_account_iam_member" "deployer_wif" {
  service_account_id = google_service_account.deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repository}"
}
