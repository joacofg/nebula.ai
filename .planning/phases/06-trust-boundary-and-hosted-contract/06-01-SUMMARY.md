---
phase: 06-trust-boundary-and-hosted-contract
plan: "01"
subsystem: api
tags: [pydantic, json-schema, trust-boundary, hosted-contract, metadata]

# Dependency graph
requires:
  - phase: 04-governance-hardening
    provides: "Pydantic model patterns and governance model conventions"
provides:
  - "HostedDeploymentMetadata canonical Pydantic model"
  - "FreshnessStatus literal (connected/degraded/stale/offline)"
  - "HOSTED_EXCLUDED_DATA_CLASSES exclusion tuple"
  - "HostedDependencySummary and HostedRemoteActionSummary sub-models"
  - "Committed JSON schema artifact at docs/hosted-default-export.schema.json"
  - "10 regression tests locking the trust-boundary contract"
affects: [07-deployment-enrollment, 08-hosted-inventory, 09-remote-management, 10-pilot-docs]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Metadata-only hosted export contract with explicit exclusion list"]

key-files:
  created:
    - src/nebula/models/hosted_contract.py
    - docs/hosted-default-export.schema.json
    - tests/test_hosted_contract.py
  modified:
    - src/nebula/models/__init__.py

key-decisions:
  - "Contract model uses Pydantic BaseModel with Literal enum for freshness, matching existing governance model patterns"
  - "Exclusion list is a plain tuple constant for simple regression testing rather than a runtime enforcement mechanism"
  - "JSON schema artifact committed to docs/ for downstream consumer reference without requiring Python imports"

patterns-established:
  - "Trust-boundary contract pattern: allowlist model + exclusion constant + committed schema artifact + drift tests"

requirements-completed: [TRST-02]

# Metrics
duration: 2min
completed: 2026-03-21
---

# Phase 6 Plan 01: Hosted Default-Export Contract Summary

**Pydantic-canonical hosted metadata contract with 6-item exclusion list, 4-value freshness enum, and committed JSON schema artifact locked by 10 regression tests**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-21T15:43:33Z
- **Completed:** 2026-03-21T15:45:33Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Canonical HostedDeploymentMetadata model defines the exact metadata a self-hosted deployment exports to the hosted control plane by default
- Explicit exclusion list (raw_prompts, raw_responses, provider_credentials, raw_usage_ledger_rows, tenant_secrets, authoritative_runtime_policy_state) prevents trust-boundary drift
- FreshnessStatus vocabulary locked to connected/degraded/stale/offline
- Committed JSON schema artifact enables downstream consumers without Python dependency
- 10 regression tests guard schema fields, freshness values, exclusion list, sub-model structure, and artifact sync

## Task Commits

Each task was committed atomically:

1. **Task 1: Write the failing trust-boundary contract tests** - `b9f446c` (test)
2. **Task 2: Implement the canonical hosted default-export contract and committed schema artifact** - `d97be67` (feat)

## Files Created/Modified
- `src/nebula/models/hosted_contract.py` - Canonical hosted export models, exclusion list, and freshness enum
- `src/nebula/models/__init__.py` - Re-exports for hosted contract symbols
- `docs/hosted-default-export.schema.json` - Committed JSON schema artifact for downstream consumers
- `tests/test_hosted_contract.py` - 10 regression tests locking the trust boundary

## Decisions Made
- Contract model uses Pydantic BaseModel with Literal enum for freshness, consistent with existing governance model patterns in `src/nebula/models/governance.py`
- Exclusion list is a plain tuple constant for simple regression testing rather than a runtime enforcement mechanism; enforcement happens at the export boundary in later phases
- JSON schema artifact committed to `docs/` so downstream doc, UI, and integration work can reference a stable file without importing Python

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None - all models are fully defined with real types and defaults.

## Next Phase Readiness
- HostedDeploymentMetadata is ready for Phase 7 (enrollment) to use as the canonical metadata shape
- FreshnessStatus vocabulary is ready for Phase 8 (hosted inventory) freshness rendering
- Exclusion list is ready for any hosted export boundary to enforce
- JSON schema artifact is available for docs and UI work in Phases 8 and 10

## Self-Check: PASSED

All 5 files found. Both commit hashes verified.

---
*Phase: 06-trust-boundary-and-hosted-contract*
*Completed: 2026-03-21*
