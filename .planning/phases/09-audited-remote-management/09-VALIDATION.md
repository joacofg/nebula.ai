---
phase: 9
slug: audited-remote-management
status: passed
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-22
updated: 2026-03-23
---

# Phase 09 — Validation Report

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest` + `vitest` |
| **Quick run command** | `pytest tests/test_remote_management_api.py tests/test_remote_management_service.py tests/test_remote_management_audit.py -x` |
| **Full suite command** | `pytest tests/test_remote_management_api.py tests/test_remote_management_service.py tests/test_remote_management_audit.py -x && npm --prefix console run test -- --run src/components/deployments/remote-action-card.test.tsx src/lib/admin-api.test.ts` |
| **Estimated runtime** | ~45 seconds |

## Wave 0 Coverage

- `tests/test_remote_management_api.py` covers hosted queue/history behavior for `RMGT-01`.
- `tests/test_remote_management_service.py` covers outbound polling, local authorization, completion, and rotated-credential acceptance for `RMGT-02`.
- `tests/test_remote_management_audit.py` covers expiry, duplicate suppression, and deployment summary rollups for `RMGT-03`.
- `console/src/components/deployments/remote-action-card.test.tsx` and `console/src/lib/admin-api.test.ts` cover the hosted console action surface.

## Evidence

- `09-VERIFICATION.md` now records the phase as `passed`.
- `09-HUMAN-UAT.md` records a live browser queue flow and a live hosted-to-gateway credential rotation.
- The hosted plane recorded action `89c0d98d-18d1-4d0c-ae76-ba80bcc9f7dd` as `applied`, and the hosted and gateway SQLite stores both finished with credential prefix `nbdc_5MLEug2`.

## Manual Verification

- Hosted drawer queue flow: completed in `09-HUMAN-UAT.md`.
- End-to-end rotation handshake across two live Nebula processes: completed in `09-HUMAN-UAT.md`.

## Validation Sign-Off

- [x] All tasks have automated verification or shipped Wave 0 coverage
- [x] Sampling continuity is satisfied
- [x] Wave 0 covers all previously missing references
- [x] No watch-mode flags are required for validation
- [x] Feedback latency stays within the declared target
- [x] `nyquist_compliant: true` is set in frontmatter

**Approval:** approved 2026-03-23
