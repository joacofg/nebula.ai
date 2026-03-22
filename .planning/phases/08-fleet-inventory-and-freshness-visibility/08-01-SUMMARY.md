---
phase: 08-fleet-inventory-and-freshness-visibility
plan: "01"
subsystem: heartbeat-ingest
tags: [heartbeat, freshness, fleet-inventory, deployment, migration]
dependency_graph:
  requires: []
  provides:
    - POST /v1/heartbeat endpoint with deployment credential auth
    - compute_freshness() with D-08 thresholds
    - HeartbeatIngestService.record_heartbeat()
    - DeploymentRecord freshness fields in all deployment API responses
    - TypeScript FreshnessStatus and DependencySummary types
  affects:
    - src/nebula/services/enrollment_service.py (_to_record)
    - src/nebula/models/deployment.py (DeploymentRecord)
    - console/src/lib/admin-api.ts (DeploymentRecord TS type)
tech_stack:
  added:
    - heartbeat_ingest_service (new service module)
    - Alembic migration 20260322_0003 (last_seen_at + dependency_summary_json columns)
  patterns:
    - Same credential-is-auth pattern as enrollment exchange endpoint (no require_admin)
    - SHA-256 hash comparison for deployment credential verification
    - Freshness computed on-read from last_seen_at (never stored)
    - Idempotent migration guard with inspector.get_columns()
key_files:
  created:
    - src/nebula/models/heartbeat.py
    - src/nebula/services/heartbeat_ingest_service.py
    - src/nebula/api/routes/heartbeat.py
    - migrations/versions/20260322_0003_last_seen_at.py
  modified:
    - src/nebula/db/models.py
    - src/nebula/models/deployment.py
    - src/nebula/services/enrollment_service.py
    - src/nebula/core/container.py
    - src/nebula/main.py
    - console/src/lib/admin-api.ts
decisions:
  - "Freshness is str | None (not Literal) in DeploymentRecord so None represents pending deployments without a false status (D-14)"
  - "HeartbeatRequest omits freshness_status field — hosted plane computes freshness from last_seen_at, not from gateway self-report (D-07)"
  - "record_heartbeat returns bool rather than raising exceptions — 401 is an expected operational case not an error"
  - "Migration revision uses full datestamp format 20260322_0003 matching existing migrations (not short 0003)"
metrics:
  duration: "2m 14s"
  completed: "2026-03-22"
  tasks_completed: 2
  files_changed: 10
requirements:
  - INVT-01
  - INVT-02
  - INVT-04
---

# Phase 08 Plan 01: Heartbeat Ingest Infrastructure Summary

## One-liner

Hosted-side heartbeat ingest with SHA-256 credential auth, D-08 freshness thresholds (connected/degraded/stale/offline), and on-read freshness computation surfaced in all deployment API responses.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Heartbeat models, DB schema, ingest service, and freshness computation | 8a749ae | heartbeat.py, deployment.py, db/models.py, heartbeat_ingest_service.py, enrollment_service.py, migration 0003 |
| 2 | Heartbeat endpoint, container registration, router wiring, and TypeScript types | b4ea3ea | heartbeat.py (route), container.py, main.py, admin-api.ts |

## What Was Built

### Pydantic Models (`src/nebula/models/heartbeat.py`)
`HeartbeatRequest` captures `nebula_version`, `capability_flags`, and `dependency_summary` from gateway heartbeats. No `freshness_status` field per D-07 — the hosted plane computes freshness, the gateway does not self-report it. `HeartbeatResponse` returns `acknowledged: bool`.

### DB Schema (`src/nebula/db/models.py` + migration)
Added `last_seen_at` (nullable DateTime with timezone) and `dependency_summary_json` (nullable JSON) columns to `DeploymentModel` after `unlinked_at`. Migration `20260322_0003` uses idempotent column guards via `inspector.get_columns()`.

### Freshness Computation (`src/nebula/services/heartbeat_ingest_service.py`)
`compute_freshness(last_seen_at)` returns `(None, None)` for pending deployments (D-14). For enrolled deployments: connected (<= 10 min), degraded (<= 30 min), stale (<= 1 hr), offline (> 1 hr). Delta is clamped with `max(delta, timedelta(0))` for clock skew safety.

### Heartbeat Ingest Service
`HeartbeatIngestService.record_heartbeat()` accepts a raw deployment credential, SHA-256 hashes it, looks up the active deployment, and updates `last_seen_at`, `nebula_version`, `capability_flags_json`, and `dependency_summary_json`. Returns `False` (not raises) for invalid credentials.

### Extended DeploymentRecord
`src/nebula/models/deployment.py` DeploymentRecord has four new optional fields: `last_seen_at`, `freshness_status`, `freshness_reason`, `dependency_summary`. `enrollment_service.py _to_record()` calls `compute_freshness()` and populates all four fields on every list/get response.

### Heartbeat Endpoint (`POST /v1/heartbeat`)
No `require_admin` dependency — deployment credential IS the auth (same pattern as `/v1/enrollment/exchange`). Reads `X-Nebula-Deployment-Credential` header, delegates to `container.heartbeat_ingest_service`, returns 401 on invalid credential.

### TypeScript Types
Added `FreshnessStatus` union type and `DependencySummary` shape type to `admin-api.ts`. Extended `DeploymentRecord` with all four freshness fields for frontend consumption in Plan 08-03.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all data fields are wired to real DB columns and computed from real heartbeat ingestion. The `dependency_summary` field will be `null` until a gateway sends its first heartbeat, which is intentional and expected behavior for pending deployments.

## Self-Check: PASSED

- `/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/models/heartbeat.py` — FOUND
- `/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/services/heartbeat_ingest_service.py` — FOUND
- `/Users/joaquinfernandezdegamboa/Proj/nebula/src/nebula/api/routes/heartbeat.py` — FOUND
- `/Users/joaquinfernandezdegamboa/Proj/nebula/migrations/versions/20260322_0003_last_seen_at.py` — FOUND
- Commit 8a749ae — FOUND
- Commit b4ea3ea — FOUND
- 75 tests passed, 0 failures
