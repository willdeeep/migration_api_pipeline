# Architecture

> Placeholder — expanded in Phase 6. The authoritative design currently lives in
> the working spec (`.opencode/specs/2026-06-27-migration-api-pipeline-design.md`)
> and the [README](../README.md).

## Overview

Extract → Validate → Transform → Load, from the Ducks Unlimited ArcGIS Feature
Service into a BigQuery migration target, run daily as a Cloud Run Job.

## To be documented

- Component diagram and data flow
- Schema mapping (source attributes → target columns)
- Failure modes and retry/idempotency behaviour
- GCP resource topology (Artifact Registry, BigQuery, Cloud Run Job, Scheduler, WIF)
