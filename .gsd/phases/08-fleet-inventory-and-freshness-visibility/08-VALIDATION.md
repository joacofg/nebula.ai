---
phase: 8
slug: fleet-inventory-and-freshness-visibility
status: passed
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-22
updated: 2026-03-23
---

# Phase 08 — Validation Report

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest` + `vitest` |
| **Quick run command** | `pytest tests/test_heartbeat_api.py tests/test_freshness.py -x` |
| **Full suite command** | `pytest tests/test_heartbeat_api.py tests/test_freshness.py -x && npm --prefix console run test -- --run src/components/deployments/freshness-badge.test.tsx src/components/deployments/deployment-table.test.tsx` |
| **Estimated runtime** | ~30 seconds |

## Wave 0 Coverage

- `tests/test_heartbeat_api.py` covers heartbeat ingest, last-seen updates, version/capability persistence, and deployment projections.
- `tests/test_freshness.py` covers threshold transitions, reason formatting, and SQLite timestamp normalization behavior for `INVT-02`.
- `console/src/components/deployments/freshness-badge.test.tsx` and `console/src/components/deployments/deployment-table.test.tsx` cover the frontend rendering path.

## Evidence

- `08-VERIFICATION.md` records the phase as `passed` with 9/9 truths verified.
- The plan summaries now explicitly list `INVT-02` in `requirements-completed`, closing the frontmatter drift called out by the milestone audit.
- Live browser inspection on 2026-03-23 confirmed the deployment table columns and the deployment drawer structure are rendered in the shipped console.

## Manual Verification

- Deployment table layout and drawer ordering: completed by live console inspection.
- The remaining visual states are adequately covered by shipped component tests and the verified deployment UI wiring.

## Validation Sign-Off

- [x] All tasks have automated verification or shipped Wave 0 coverage
- [x] Sampling continuity is satisfied
- [x] Wave 0 covers all previously missing references
- [x] No watch-mode flags are required for validation
- [x] Feedback latency stays within the declared target
- [x] `nyquist_compliant: true` is set in frontmatter

**Approval:** approved 2026-03-23
