---
id: T03
parent: S02
milestone: M006
provides: []
requires: []
affects: []
key_files: ["src/nebula/models/governance.py", "src/nebula/services/recommendation_service.py", "console/src/lib/admin-api.ts", "console/src/components/ledger/ledger-request-detail.tsx", "console/src/components/ledger/ledger-request-detail.test.tsx", "console/src/app/(console)/observability/page.tsx", "console/src/app/(console)/observability/observability-page.test.tsx"]
key_decisions: ["Extended RecommendationBundle with calibration_summary so Observability can reuse the same bounded tenant-scoped calibration contract as replay without adding a new admin surface."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran the focused console Vitest suite for ledger-request-detail and observability-page and it passed after aligning duplicate-label assertions with the final UI. LSP diagnostics were clean for src/nebula/models/governance.py and src/nebula/services/recommendation_service.py."
completed_at: 2026-04-02T03:36:39.519Z
blocker_discovered: false
---

# T03: Rendered shared ledger-backed calibration evidence on Observability and request detail surfaces without displacing the persisted request-proof story.

> Rendered shared ledger-backed calibration evidence on Observability and request detail surfaces without displacing the persisted request-proof story.

## What Happened
---
id: T03
parent: S02
milestone: M006
key_files:
  - src/nebula/models/governance.py
  - src/nebula/services/recommendation_service.py
  - console/src/lib/admin-api.ts
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/ledger/ledger-request-detail.test.tsx
  - console/src/app/(console)/observability/page.tsx
  - console/src/app/(console)/observability/observability-page.test.tsx
key_decisions:
  - Extended RecommendationBundle with calibration_summary so Observability can reuse the same bounded tenant-scoped calibration contract as replay without adding a new admin surface.
duration: ""
verification_result: passed
completed_at: 2026-04-02T03:36:39.520Z
blocker_discovered: false
---

# T03: Rendered shared ledger-backed calibration evidence on Observability and request detail surfaces without displacing the persisted request-proof story.

**Rendered shared ledger-backed calibration evidence on Observability and request detail surfaces without displacing the persisted request-proof story.**

## What Happened

Extended the shared recommendation contract so admin recommendation responses now carry the existing calibration summary derived from GovernanceStore, then mirrored that field in the console admin API types. Updated console/src/components/ledger/ledger-request-detail.tsx to render a compact calibration-evidence block that explains sufficient, stale, thin, and rollout-disabled states in operator language while keeping the selected ledger row as the primary persisted proof surface. Updated console/src/app/(console)/observability/page.tsx to show tenant-scoped calibration evidence beside grounded recommendations and cache/runtime context, explicitly framing it as bounded supporting context rather than a separate analytics view. Added focused Vitest coverage for sufficient/stale/thin/disabled messaging, absent-summary handling, and the guardrail that Observability remains ledger-first.

## Verification

Ran the focused console Vitest suite for ledger-request-detail and observability-page and it passed after aligning duplicate-label assertions with the final UI. LSP diagnostics were clean for src/nebula/models/governance.py and src/nebula/services/recommendation_service.py.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/app/'(console)'/observability/observability-page.test.tsx` | 0 | ✅ pass | 3800ms |
| 2 | `lsp diagnostics src/nebula/models/governance.py` | 0 | ✅ pass | 0ms |
| 3 | `lsp diagnostics src/nebula/services/recommendation_service.py` | 0 | ✅ pass | 0ms |


## Deviations

Added calibration_summary to RecommendationBundle and RecommendationService because the task-required Observability surface needed the shared bounded calibration contract but the existing recommendation response had not been extended yet.

## Known Issues

None.

## Files Created/Modified

- `src/nebula/models/governance.py`
- `src/nebula/services/recommendation_service.py`
- `console/src/lib/admin-api.ts`
- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`
- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`


## Deviations
Added calibration_summary to RecommendationBundle and RecommendationService because the task-required Observability surface needed the shared bounded calibration contract but the existing recommendation response had not been extended yet.

## Known Issues
None.
