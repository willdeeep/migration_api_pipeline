# CI/CD

GitHub Actions workflows: [ci.yml](../.github/workflows/ci.yml) (the merge gate)
and [deploy.yml](../.github/workflows/deploy.yml) (release on merge to `main`).

## Pipeline

```
PR / push ──► quality ──► (push to main only, if enabled) ──► deploy
              ruff                                            WIF auth (keyless)
              ruff format                                     ensure Artifact Registry
              mypy                                            build + push image (:sha, :latest)
              pytest (unit)                                   terraform apply (new job revision)
                                                              execute job (smoke test)
```

- **CI** (`ci.yml`) — the `quality` job runs on every PR and feature-branch push;
  it is the required status check that gates merging to `main`.
- **Deploy** (`deploy.yml`) — runs on push to `main` (i.e. a merged PR), and only
  when `DEPLOY_ENABLED == 'true'` so it stays inert until infra is wired up. Auth
  to GCP is short-lived OIDC via **Workload Identity Federation** — no JSON keys.

## Branching model & environments

This project uses a deliberately **simplified single-branch workflow**: one
long-lived, protected, PR-only branch (`main`) that deploys to a **single
production environment**. Every merge to `main` ships to prod. That keeps the
assessment easy to run and reason about.

**In a collaborative, multi-developer project I would promote changes through
several branches and matching environments** rather than deploying straight to
prod:

| Branch | Environment | Purpose |
|---|---|---|
| `dev` | development | integration + developer testing |
| `staging` | staging | UAT / pre-production sign-off |
| `main` (prod) | production | released, live workloads |

Changes flow **dev → staging → main** via PRs, with UAT sign-off gating the
staging → main promotion. Each environment would be isolated — its own GCP
project (or clearly separated resources), its own Terraform state, its own Secret
Manager values and image tags — and the Deploy workflow would target the
environment matching the branch (e.g. GitHub Actions Environments with
per-environment Variables and required reviewers on prod). It's a natural
extension of what's here: the same `deploy.yml`, parameterised per environment
and triggered on merges into each branch.

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
