# Contributing

`main` is protected: it accepts changes **only via pull request**, and a PR can
merge only when the **CI** check is green.

## Workflow

1. Branch off `main` using a typed prefix:
   - `feature/<slug>` — new functionality
   - `bugfix/<slug>` — fixes
   - `refactor/<slug>` — internal changes, no behaviour change
   - `docs/<slug>` — documentation
   - `chore/<slug>` — tooling, deps, CI, housekeeping
2. Commit your work (pre-commit gates each commit — see below).
3. Push the branch and open a PR into `main`.
4. CI runs `ruff format --check`, `ruff check`, `mypy`, and `pytest`. The PR
   merges once CI passes.
5. **Squash-merge** to keep `main` history linear.

When a PR merges into `main`, the **Deploy** workflow builds the image, applies
Terraform, deploys a new Cloud Run Job revision, and runs the job as a smoke test
(only when deployment is enabled — see [docs/cicd.md](docs/cicd.md)).

## Local setup

```bash
uv sync                       # install deps (incl. dev tools)
uv run pre-commit install     # enable the commit-time quality gate
```

## Pre-commit

Every commit runs the same fast checks CI enforces, so problems surface locally:

- `ruff format --check`
- `ruff check` (includes import ordering)
- `mypy`
- `pytest -m "not integration"`

Run them on demand with `uv run pre-commit run --all-files`. Integration tests
(which need GCP credentials) are excluded from the fast gate and run separately.
