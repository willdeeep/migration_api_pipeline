# Reusable, least-privilege "profile" for people reviewing the deployed pipeline.
#
# This defines ONLY the permission grouping (a custom role). Assigning individual
# reviewers to it is done by hand in the Cloud Console (IAM -> Grant access), so
# no member emails ever live in this (public) repo. Custom-role creation needs
# owner-level iam.roles.create, which is why this sits in the human-applied
# bootstrap layer rather than the CI-applied main layer.
resource "google_project_iam_custom_role" "assessor" {
  role_id     = "migrationAssessor"
  title       = "Migration Pipeline Assessor (read-only)"
  description = "Read-only access to verify the deployed migration pipeline: query the BigQuery target and view Cloud Run executions, Cloud Scheduler, logs, and images. No write access; no secret access."

  permissions = [
    # See the project.
    "resourcemanager.projects.get",

    # BigQuery — read and query the migrated data.
    "bigquery.datasets.get",
    "bigquery.tables.get",
    "bigquery.tables.list",
    "bigquery.tables.getData",
    "bigquery.jobs.create",

    # Cloud Run — view the job and its executions.
    "run.jobs.get",
    "run.jobs.list",
    "run.executions.get",
    "run.executions.list",
    "run.locations.list",

    # Cloud Scheduler — view the daily trigger.
    "cloudscheduler.jobs.get",
    "cloudscheduler.jobs.list",
    "cloudscheduler.locations.list",

    # Cloud Logging — read run output.
    "logging.logEntries.list",
    "logging.logs.list",

    # Artifact Registry — view the built images.
    "artifactregistry.repositories.get",
    "artifactregistry.repositories.list",
    "artifactregistry.dockerimages.list",

    # IAM / access design — inspect the least-privilege setup: roles, service
    # accounts, Workload Identity Federation, and who is granted what (project-
    # and resource-level policies). Read-only: no policy changes.
    "resourcemanager.projects.getIamPolicy",
    "iam.roles.get",
    "iam.roles.list",
    "iam.serviceAccounts.get",
    "iam.serviceAccounts.list",
    "iam.workloadIdentityPools.get",
    "iam.workloadIdentityPools.list",
    "iam.workloadIdentityPoolProviders.get",
    "iam.workloadIdentityPoolProviders.list",
    "run.jobs.getIamPolicy",
    "secretmanager.secrets.getIamPolicy",
    "artifactregistry.repositories.getIamPolicy",

    # Cloud Storage — see the Terraform state bucket and its config (metadata
    # only, not object contents).
    "storage.buckets.get",
    "storage.buckets.list",
  ]
}

output "assessor_role_id" {
  value       = google_project_iam_custom_role.assessor.role_id
  description = "Grant this custom role to reviewers in the Console (IAM -> Grant access). No members are managed in Terraform."
}
