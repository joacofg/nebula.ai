---
id: T01
parent: S04
milestone: M009
key_files:
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/ledger/ledger-request-detail.test.tsx
key_decisions:
  - Normalized selected-request routing wording around grounded/degraded/rollout-disabled/unscored states derived from persisted `route_signals`.
  - Kept tenant `calibration_summary` strictly subordinate to the selected request row while aligning its copy to the same vocabulary family.
duration: 
verification_result: passed
completed_at: 2026-04-27T21:21:26.476Z
blocker_discovered: false
---

# T01: Aligned request-detail routing evidence to grounded/thin/stale/degraded wording while preserving selected-row authority.

**Aligned request-detail routing evidence to grounded/thin/stale/degraded wording while preserving selected-row authority.**

## What Happened

Updated `console/src/components/ledger/ledger-request-detail.tsx` so selected-request routing inspection now speaks in one operator vocabulary anchored to persisted request evidence: grounded, degraded, rollout disabled, and unscored. Kept D051/MEM051 intact by making the selected ledger row explicitly authoritative and rewriting calibration-summary copy as supporting context only. Hardened request-detail rendering for incomplete fixtures by tolerating missing suppressed metadata arrays and optional reason arrays in supporting evidence formatting. Extended `console/src/components/ledger/ledger-request-detail.test.tsx` to assert the new grounded/thin/stale/degraded wording, rollout-disabled and unscored request states, degraded supporting-summary behavior, request-first hierarchy, and safe rendering when optional fields are absent.

## Verification

Ran the focused Vitest suite for `console/src/components/ledger/ledger-request-detail.test.tsx`. It passed 15/15 tests, confirming explicit grounded/degraded/rollout-disabled/unscored request wording, grounded/thin/stale/degraded supporting calibration wording, request-first hierarchy, and safe rendering with incomplete request fixtures.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run 'src/components/ledger/ledger-request-detail.test.tsx'` | 0 | ✅ pass | 753ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`
