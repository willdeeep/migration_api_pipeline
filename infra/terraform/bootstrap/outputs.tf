output "state_bucket" {
  value       = google_storage_bucket.tf_state.name
  description = "Pass to the main layer: terraform init -backend-config=\"bucket=<this>\"."
}

output "workload_identity_provider" {
  value       = google_iam_workload_identity_pool_provider.github.name
  description = "Full provider resource name for google-github-actions/auth in CI."
}

output "deployer_service_account" {
  value       = google_service_account.deployer.email
  description = "Service account GitHub Actions impersonates to deploy."
}
