# syntax=docker/dockerfile:1

# --- Builder: resolve and install dependencies with uv (preinstalled) ---------
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

# Byte-compile for faster startup; copy (not symlink) so the venv is relocatable;
# never reach out to download a Python — the base image already has 3.14.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# 1) Dependencies only — cached unless pyproject.toml / uv.lock change.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 2) Project — installed non-editable so the runtime needs only the venv (no src/).
COPY README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

# --- Runtime: minimal slim image, just the built virtualenv --------------------
FROM python:3.14-slim-bookworm AS runtime

# Non-root user for least privilege.
RUN useradd --create-home --uid 1000 app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY --from=builder --chown=app:app /app/.venv /app/.venv

USER app
WORKDIR /app

# One migration run per container invocation (Cloud Run Job semantics).
ENTRYPOINT ["python", "-m", "migration_pipeline"]
