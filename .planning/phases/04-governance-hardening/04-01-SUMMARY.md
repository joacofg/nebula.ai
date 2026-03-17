---
phase: 04-governance-hardening
plan: "01"
subsystem: api
tags: [fastapi, governance, policy, pytest, routing]
requires:
  - phase: 02-operator-console
    provides: admin policy editing and policy-options consumers
  - phase: 03-playground-observability
    provides: runtime metadata and policy outcome reporting
provides:
  - authoritative policy-options buckets for runtime-enforced, soft-signal, and advisory fields
  - GOV-01 runtime coverage for routing mode, cache, fallback, allowlist, and spend controls
affects: [04-02, 04-03, admin-api, console-policy-contract]
tech-stack:
  added: []
  patterns: [TDD for governance behavior, backend-authoritative policy metadata]
key-files:
  created: [tests/test_governance_runtime_hardening.py]
  modified: [src/nebula/models/governance.py, src/nebula/api/routes/admin.py, tests/test_governance_api.py, tests/test_service_flows.py]
key-decisions:
  - "The `/v1/admin/policy/options` response is the authoritative machine-readable boundary between runtime-enforced, soft-signal, and advisory policy fields."
  - "Runtime enforcement remains centralized in `PolicyService.resolve()`; the admin route only publishes contract metadata."
patterns-established:
  - "Policy contract changes must be backed by direct runtime tests, not only editable fields."
  - "Soft budget remains non-blocking and is expressed through `policy_outcome` annotations."
requirements-completed: [GOV-01]
duration: 3m
completed: 2026-03-17
---

# Phase 4 Plan 01: Align policy surface with enforced backend behavior Summary

**Authoritative policy-options field classification plus GOV-01 runtime coverage for routing modes, soft-budget signaling, and premium guardrails**

## Performance

- **Duration:** 3m
- **Started:** 2026-03-17T02:47:40Z
- **Completed:** 2026-03-17T02:50:45Z
- **Tasks:** 1
- **Files modified:** 5

## Accomplishments
- Added backend-authoritative `runtime_enforced_fields`, `soft_signal_fields`, and `advisory_fields` to the policy-options contract.
- Added requirement-level tests for routing mode behavior, explicit-model denials, premium-model allowlists, spend guardrails, and soft-budget annotations.
- Kept runtime governance enforcement in `PolicyService.resolve()` while proving the policy surface aligns with backend behavior.

## Task Commits

Each task was committed atomically:

1. **Task 1: Make the backend policy contract explicitly authoritative about runtime-enforced, soft-signal, and advisory fields** - `fa3305e` (test)
2. **Task 1: Make the backend policy contract explicitly authoritative about runtime-enforced, soft-signal, and advisory fields** - `01a01b8` (feat)

## Files Created/Modified
- `tests/test_governance_runtime_hardening.py` - Requirement-level runtime hardening matrix for policy enforcement behavior.
- `tests/test_governance_api.py` - Admin policy options assertions for runtime, soft-signal, and advisory buckets.
- `tests/test_service_flows.py` - Direct `PolicyService` coverage for cache, fallback, and soft-budget signaling.
- `src/nebula/models/governance.py` - Typed policy-options response fields for authoritative classification.
- `src/nebula/api/routes/admin.py` - Published exact backend field classifications through `/v1/admin/policy/options`.

## Decisions Made

- The policy-options endpoint now defines the authoritative classification of exposed tenant policy fields so downstream UI and tests can consume backend truth directly.
- `soft_budget_usd` remains a soft signal only; crossing it annotates `policy_outcome` with `soft_budget=exceeded` and does not deny routing by itself.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The initial RED test setup instantiated `PricingCatalog` incorrectly; the tests were corrected to load the existing benchmark pricing fixture before the final RED commit so the failing state isolated the missing contract rather than broken harness code.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase `04-02` can now harden denied-path metadata and error semantics against a stable backend policy contract.
- Phase `04-03` can consume `runtime_enforced_fields`, `soft_signal_fields`, and `advisory_fields` directly instead of inferring console copy from stored policy fields.

## Self-Check: PASSED

- Found `.planning/phases/04-governance-hardening/04-01-SUMMARY.md`
- Found commit `fa3305e`
- Found commit `01a01b8`
