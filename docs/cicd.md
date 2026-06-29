# CI/CD

GitHub Actions workflow: [.github/workflows/ci-cd.yml](../.github/workflows/ci-cd.yml).

## Pipeline

```
PR / push ──► quality ──► (push to main only, if enabled) ──► deploy
              ruff                                            WIF auth (keyless)
              ruff format                                     ensure Artifact Registry
              mypy                                            build + push image (:sha, :latest)
              pytest (unit)                                   terraform apply (new job revision)
                                                              execute job (smoke test)
```

- **quality** runs on every PR and push — the merge gate.
- **deploy** runs only on `main`, and only when `DEPLOY_ENABLED == 'true'`. Auth
  to GCP is short-lived OIDC via **Workload Identity Federation** — no JSON keys.

## Dependency: apply the bootstrap layer first

`deploy` impersonates the `tf-deployer` service account through the WIF provider,
both created by [infra/terraform/bootstrap](../infra/terraform/bootstrap). Apply
that layer once (locally, with ADC) before enabling deploy.

## Enablement checklist

After `bootstrap` is applied, set these **repository Variables**
(Settings → Secrets and variables → Actions → Variables):

| Variable | Value |
|---|---|
| `DEPLOY_ENABLED` | `true` |
| `GCP_PROJECT` | `migration-api-pipeline` |
| `GCP_REGION` | `us-central1` |
| `AR_REPO` | `migration` |
| `TF_STATE_BUCKET` | bootstrap output `state_bucket` |
| `WIF_PROVIDER` | bootstrap output `workload_identity_provider` |
| `DEPLOYER_SA` | bootstrap output `deployer_service_account` |
| `MIGRATION_SOURCE_URL` | ArcGIS FeatureServer query endpoint |

Set them quickly with `gh`:

```bash
gh variable set DEPLOY_ENABLED --body true
gh variable set GCP_PROJECT --body migration-api-pipeline
gh variable set GCP_REGION --body us-central1
gh variable set AR_REPO --body migration
gh variable set TF_STATE_BUCKET --body "$(terraform -chdir=infra/terraform/bootstrap output -raw state_bucket)"
gh variable set WIF_PROVIDER --body "$(terraform -chdir=infra/terraform/bootstrap output -raw workload_identity_provider)"
gh variable set DEPLOYER_SA --body "$(terraform -chdir=infra/terraform/bootstrap output -raw deployer_service_account)"
gh variable set MIGRATION_SOURCE_URL --body "https://services2.arcgis.com/5I7u4SJE1vUr79JC/arcgis/rest/services/UniversityChapters_Public/FeatureServer/0/query"
```

These are non-sensitive configuration, so repository Variables (not Secrets) are
appropriate. The only true secret — the source endpoint at runtime — is stored in
Secret Manager by Terraform and injected into the job.

## Why a smoke test on deploy

Executing the job after apply proves the new image actually runs end-to-end
against BigQuery, so a broken build fails the pipeline rather than silently
shipping a non-working revision.
