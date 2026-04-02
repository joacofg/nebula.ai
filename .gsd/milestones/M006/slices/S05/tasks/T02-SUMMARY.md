---
id: T02
parent: S05
milestone: M006
provides: []
requires: []
affects: []
key_files: ["tests/test_governance_api.py", "console/src/app/(console)/observability/page.test.tsx", "console/src/app/(console)/observability/observability-page.test.tsx", "console/src/components/policy/policy-page.test.tsx", ".gsd/milestones/M006/slices/S05/tasks/T02-SUMMARY.md"]
key_decisions: ["Reused the existing calibrated-routing and operator-page test seams instead of adding a new integrated harness, and tightened them to assert the close-out proof order directly."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran the exact focused verification sequence from the task plan. `./.venv/bin/pytest tests/test_response_headers.py -x` passed, confirming the public header seam still exposes calibrated routing metadata. `./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x` passed, confirming request-id ledger correlation plus replay and rollout-disabled semantics in the tightened backend proof path. `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-page.test.tsx` passed, confirming selected-request-first Observability framing and bounded policy preview wording in the console."
completed_at: 2026-04-02T04:25:47.316Z
blocker_discovered: false
---

# T02: Locked the assembled M006 proof path with focused backend and console verification.

> Locked the assembled M006 proof path with focused backend and console verification.

## What Happened
---
id: T02
parent: S05
milestone: M006
key_files:
  - tests/test_governance_api.py
  - console/src/app/(console)/observability/page.test.tsx
  - console/src/app/(console)/observability/observability-page.test.tsx
  - console/src/components/policy/policy-page.test.tsx
  - .gsd/milestones/M006/slices/S05/tasks/T02-SUMMARY.md
key_decisions:
  - Reused the existing calibrated-routing and operator-page test seams instead of adding a new integrated harness, and tightened them to assert the close-out proof order directly.
duration: ""
verification_result: passed
completed_at: 2026-04-02T04:25:47.317Z
blocker_discovered: false
---

# T02: Locked the assembled M006 proof path with focused backend and console verification.

**Locked the assembled M006 proof path with focused backend and console verification.**

## What Happened

Tightened the existing calibrated-routing proof seams rather than adding a new harness. In tests/test_governance_api.py, the close-out simulation path now asserts one calibrated public request through X-Request-ID, calibrated X-Nebula-* headers, the correlated usage-ledger row, replay changed-request parity, and the bounded rollout-disabled runtime case after the policy flip. In the console test suite, I tightened the existing Observability and Policy page assertions so the selected request remains primary, supporting context stays subordinate, and replay preview remains a compact changed-request sample instead of reading like a broader analytics or tuning surface. No runtime code changes were required because the shipped behavior already matched the integrated proof doc; this task makes that assembled story executable in the current worktree.

## Verification

Ran the exact focused verification sequence from the task plan. `./.venv/bin/pytest tests/test_response_headers.py -x` passed, confirming the public header seam still exposes calibrated routing metadata. `./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x` passed, confirming request-id ledger correlation plus replay and rollout-disabled semantics in the tightened backend proof path. `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-page.test.tsx` passed, confirming selected-request-first Observability framing and bounded policy preview wording in the console.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_response_headers.py -x` | 0 | ✅ pass | 1410ms |
| 2 | `./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x` | 0 | ✅ pass | 740ms |
| 3 | `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-page.test.tsx` | 0 | ✅ pass | 1180ms |


## Deviations

None.

## Known Issues

A pre-existing Ruff diagnostic reports a duplicate test name in tests/test_governance_api.py outside the M006 close-out seam touched here. The focused verification for this task still passed, so I left that unrelated warning unchanged.

## Files Created/Modified

- `tests/test_governance_api.py`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`
- `.gsd/milestones/M006/slices/S05/tasks/T02-SUMMARY.md`


## Deviations
None.

## Known Issues
A pre-existing Ruff diagnostic reports a duplicate test name in tests/test_governance_api.py outside the M006 close-out seam touched here. The focused verification for this task still passed, so I left that unrelated warning unchanged.
