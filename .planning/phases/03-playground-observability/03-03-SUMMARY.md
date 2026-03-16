---
phase: 03-playground-observability
plan: "03"
subsystem: observability
tags: [health, usage-ledger, nextjs, fastapi, playwright]
requires:
  - 03-01
provides:
  - Premium-provider health as part of the backend runtime dependency contract
  - Operator observability page with usage-ledger filters and adjacent request detail
  - Runtime health cards and browser coverage for degraded optional dependencies
affects: [runtime-health, observability-ui, usage-ledger, testing]
tech-stack:
  added: []
  patterns: [same-origin health proxy, list-and-detail observability layout, explicit degraded-optional messaging]
key-files:
  created:
    - src/nebula/services/premium_provider_health_service.py
    - console/src/app/(console)/observability/page.tsx
    - console/src/components/ledger/ledger-filters.tsx
    - console/src/components/ledger/ledger-table.tsx
    - console/src/components/ledger/ledger-request-detail.tsx
    - console/src/components/health/runtime-health-cards.tsx
    - console/src/components/health/runtime-health-cards.test.tsx
    - console/src/app/api/runtime/health/route.ts
    - console/e2e/observability.spec.ts
  modified:
    - src/nebula/core/container.py
    - src/nebula/services/runtime_health_service.py
    - tests/test_health.py
    - console/src/app/(console)/observability/page.tsx
key-decisions:
  - "Premium-provider readiness is exposed as an optional dependency so degraded upstream reachability does not falsely mark the whole gateway unavailable."
  - "Observability stays focused on a ledger workflow plus dependency state, not charts or aggregate dashboards."
  - "The console fetches runtime health through a same-origin proxy to the public backend endpoint rather than reusing admin-key auth."
patterns-established:
  - "Dependency cards always show literal backend status text and detail copy instead of relying on color alone."
  - "Optional dependency degradation gets an explicit gateway-readiness message whenever any optional dependency is degraded."
requirements-completed: [OBS-01, OBS-02]
duration: 6 min
completed: 2026-03-16
---

# Phase 03-03 Summary

**Usage-ledger observability and runtime dependency health in the operator console**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-16T19:36:11-03:00
- **Completed:** 2026-03-16T19:42:29-03:00
- **Tasks:** 3
- **Files modified:** 14

## Accomplishments

- Added backend-owned premium-provider health probing and extended `/health/dependencies` so runtime status now includes `premium_provider` alongside the existing dependency set.
- Built the `/observability` console route with tenant, route-target, terminal-status, and time-window filters plus a detail panel for recorded request metadata and token/cost fields.
- Added runtime health cards and browser coverage that prove optional premium-provider degradation is visible without implying gateway unavailability.

## Verification

- `./.venv/bin/pytest tests/test_health.py -q`
- `npm --prefix console run test -- --run ledger-filters ledger-table`
- `npm --prefix console run test -- --run runtime-health-cards`
- `npm --prefix console run e2e -- observability.spec.ts`

## Task Commits

1. **Task 1: Extend the backend runtime health contract with premium-provider status** - `f9665d5`
2. **Task 2: Build the observability ledger view with tenant, route-target, terminal-status, and time-window filters** - `0c7f217`
3. **Task 3: Add dependency-health cards and observability browser coverage** - `0838221`

## Notes

- `OBS-01` is complete through the filtered ledger workflow and request-detail panel.
- `OBS-02` is complete because the console now surfaces readiness and degradation for cache, local Ollama, and premium-provider dependencies.

## Self-Check: PASSED
