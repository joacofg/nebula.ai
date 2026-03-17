---
phase: 04-governance-hardening
plan: "03"
subsystem: ui
tags: [console, governance, policy, react, playwright, vitest]
requires:
  - phase: 04-02
    provides: Denied-path governance contract and backend-authored policy metadata
provides:
  - Typed console policy options for runtime-enforced, soft-signal, and advisory fields
  - Phase 4 policy editor UI derived from backend field classifications
  - Browser coverage for runtime, soft-signal, and deferred capture wording
affects: [frontend, operator-console, governance]
tech-stack:
  added: []
  patterns: [backend-driven policy form rendering, exact-string governance contract coverage]
key-files:
  created: []
  modified:
    - console/src/lib/admin-api.ts
    - console/src/components/policy/policy-form.tsx
    - console/src/components/policy/policy-advanced-section.tsx
    - console/src/components/policy/policy-form.test.tsx
    - console/src/components/policy/policy-page.test.tsx
    - console/e2e/policy.spec.ts
key-decisions:
  - "The console treats /v1/admin/policy/options as the only source of truth for which policy fields are runtime-enforced."
  - "Prompt and response capture settings remain in the persisted payload but are represented only as deferred explanatory copy in Phase 4."
patterns-established:
  - "Policy UI sections derive from backend classification metadata instead of duplicating a frontend policy truth table."
  - "Component and Playwright coverage pin exact governance wording so console/backend drift fails tests quickly."
requirements-completed: [GOV-01]
duration: 6 min
completed: 2026-03-17
---

# Phase 04 Plan 03: Policy Contract Alignment Summary

**Backend-driven Phase 4 policy editor wording with runtime-only controls, soft-budget signal copy, and deferred capture settings coverage**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-17T03:03:00Z
- **Completed:** 2026-03-17T03:08:41Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Typed the console `PolicyOptionsResponse` to include runtime-enforced, soft-signal, and advisory policy fields from the backend contract.
- Reworked the policy editor so visible controls are driven by `runtime_enforced_fields`, `soft_budget_usd` stays outside that section with exact soft-signal copy, and capture settings are non-editable deferred copy only.
- Extended component and Playwright coverage to fail on wording drift while preserving the existing explicit save flow.

## Task Commits

Each task was committed atomically:

1. **Task 1: Type the console policy contract and align runtime-vs-advisory UI copy** - `2c59918`, `faa08e9`
2. **Task 2: Extend browser coverage for the Phase 4 policy contract wording** - `7c43552`, `63524c0`

_Note: TDD tasks used separate RED and GREEN commits._

## Files Created/Modified
- `console/src/lib/admin-api.ts` - Added the typed backend field-classification metadata to the console policy options contract.
- `console/src/components/policy/policy-form.tsx` - Derived visible controls from backend metadata, preserved advisory values in saves, and moved soft-budget treatment out of runtime-enforced controls.
- `console/src/components/policy/policy-advanced-section.tsx` - Replaced editable capture controls with exact deferred Phase 4 explanatory copy.
- `console/src/components/policy/policy-form.test.tsx` - Added assertions for runtime-enforced grouping and soft-budget copy.
- `console/src/components/policy/policy-page.test.tsx` - Added assertions for deferred capture copy and hidden capture controls.
- `console/e2e/policy.spec.ts` - Updated browser mocks and assertions to cover the new contract wording while keeping save verification.

## Decisions Made

- The console now preserves advisory policy fields by spreading the existing backend payload into saves instead of re-rendering advisory toggles on the page.
- Runtime-enforced and soft-signal presentation is contract-driven, so future backend classification changes surface through the same typed options response.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The initial Playwright section locator was too broad and matched soft-budget text outside the runtime section; tightening the selector to the nearest ancestor section resolved the false failure without changing product code.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 4 now ends with console wording and browser coverage aligned to the backend governance boundary.
- No blockers found for advancing beyond `04-03`.

## Self-Check: PASSED

- Found `.planning/phases/04-governance-hardening/04-03-SUMMARY.md`
- Verified commits `2c59918`, `faa08e9`, `7c43552`, and `63524c0`
