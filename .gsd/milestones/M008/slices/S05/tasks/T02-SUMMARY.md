---
id: T02
parent: S05
milestone: M008
key_files:
  - tests/test_health.py
  - console/src/app/(console)/observability/page.test.tsx
key_decisions:
  - Preserved the existing proof seams and added only ordering assertions where the integrated-governance contract was still implicit.
  - Kept retention lifecycle verification subordinate to governance-store and selected-request evidence instead of introducing new runtime surfaces or broader feature changes.
duration: 
verification_result: passed
completed_at: 2026-04-12T17:29:02.684Z
blocker_discovered: false
---

# T02: Tightened integrated-governance proof tests to lock request-evidence-first and supporting-health ordering.

**Tightened integrated-governance proof tests to lock request-evidence-first and supporting-health ordering.**

## What Happened

I executed the focused backend and console suites that encode the M008 integrated governance proof and confirmed the existing seams already covered persistence truth, governed deletion semantics, coarse hosted metadata-only boundaries, and console copy around retained/suppressed/deleted/not-hosted evidence. Instead of widening scope, I added only two narrow regression assertions where the integrated proof ordering was still implicit rather than mechanically pinned. In `tests/test_health.py`, I tightened the readiness/dependencies check so `retention_lifecycle` is explicitly verified as following `governance_store`, preserving the contract that runtime health remains supporting context after the primary local evidence seam. In `console/src/app/(console)/observability/page.test.tsx`, I added ordering assertions that the selected request evidence section appears before the follow-up context section and that persisted request-row content is encountered before the `retention_lifecycle` runtime-health surface, locking the request-evidence-first investigation flow described by `docs/m008-integrated-proof.md`. No endpoints, dashboards, exports, or hosted scope changed; this task only made the assembled proof path more executable and reviewable.

## Verification

Ran the task’s required focused verification command twice: once to establish the current seam coverage and again after the minimal assertion updates. Backend pytest passed for usage-ledger, retention lifecycle, health, and hosted heartbeat coverage. Console Vitest passed for ledger request detail, runtime health cards, observability page ordering, trust-boundary card, and trust-boundary page wording. The final passing runs confirm that request detail remains authoritative while a row exists, governed deletion still removes rows without soft-delete/recovery implications, retention lifecycle health remains supporting runtime context, and hosted wording stays metadata-only and non-authoritative.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_governance_api.py tests/test_retention_lifecycle_service.py tests/test_health.py tests/test_hosted_contract.py -k "usage_ledger or retention or lifecycle or health or heartbeat"` | 0 | ✅ pass | 3070ms |
| 2 | `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/components/health/runtime-health-cards.test.tsx 'src/app/(console)/observability/page.test.tsx' src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx` | 0 | ✅ pass | 703ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `tests/test_health.py`
- `console/src/app/(console)/observability/page.test.tsx`
