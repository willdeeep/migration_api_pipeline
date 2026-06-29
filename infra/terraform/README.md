# Infrastructure (Terraform)

Provisions the migration pipeline on GCP, split into two layers:

```
bootstrap/   run ONCE, locally, with your ADC. Local state.
             -> Terraform state bucket (GCS) · enabled APIs
             -> Workload Identity Federation pool/provider for GitHub
             -> tf-deployer service account (impersonated by CI)

main/        the application infrastructure. State in the GCS bucket above.
             Run locally for the first apply, then by GitHub Actions (Phase 5).
             -> Artifact Registry (Docker)          #4
             -> BigQuery dataset + table             #5
             -> Cloud Run Job + runtime/invoker SAs  #6
             -> Cloud Scheduler (daily trigger)      #7
             -> Secret Manager (source URL)          #8
```

All authentication is OAuth / short-lived — **no JSON service-account keys** are
created or stored. The provider lock files (`.terraform.lock.hcl`) are committed
for reproducible provider versions.

## Prerequisites

- `terraform >= 1.5`, `gcloud` authenticated, and ADC:
  `gcloud auth application-default login`
- A globally-unique name for the state bucket.

## 1. Bootstrap (once)

```bash
cd bootstrap
cp terraform.tfvars.example terraform.tfvars   # edit values
terraform init
terraform apply
```

Note the outputs: `state_bucket`, `workload_identity_provider`,
`deployer_service_account`.

## 2. Main

```bash
cd ../main
cp terraform.tfvars.example terraform.tfvars    # edit values (incl. a pushed image tag)
terraform init -backend-config="bucket=<state_bucket from bootstrap>"
terraform apply
```

> Chicken-and-egg: the Cloud Run Job needs an image. Either push one first (build
> + push to the Artifact Registry path), or create the registry on a first
> `terraform apply -target=google_artifact_registry_repository.migration`, push,
> then apply the rest. From Phase 5, CI builds/pushes the image and passes its
> tag via `-var image=...`.

## Teardown

```bash
cd main && terraform destroy
cd ../bootstrap && terraform destroy   # leaves APIs enabled (disable_on_destroy=false)
```

## Verification status (Phase 4)

Both layers pass `terraform fmt`, `terraform validate`, and a read-only
`terraform plan` against the project (bootstrap: 26 to add; main: 13 to add).
No resources were applied in Phase 4 — apply is performed by the operator (and,
from Phase 5, by CI).
