---
phase: 9
slug: audited-remote-management
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest>=8.2.0,<9.0.0` + `pytest-asyncio>=0.23.0,<1.0.0`; `vitest^3.0.8` for console |
| **Config file** | `pyproject.toml`, `console/vitest.config.ts` |
| **Quick run command** | `pytest tests/test_remote_management_api.py tests/test_remote_management_service.py tests/test_remote_management_audit.py -x` |
| **Full suite command** | `make test && make console-test` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_remote_management_api.py tests/test_remote_management_service.py tests/test_remote_management_audit.py -x`
- **After every plan wave:** Run `make test && make console-test`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | RMGT-01 | integration | `pytest tests/test_remote_management_api.py -k 'queue or duplicate or invalid_state' -x` | ❌ W0 | ⬜ pending |
| 09-01-02 | 01 | 1 | RMGT-01 | unit | `pytest tests/test_remote_management_audit.py -k 'dedupe or expires' -x` | ❌ W0 | ⬜ pending |
| 09-02-01 | 02 | 2 | RMGT-02 | integration | `pytest tests/test_remote_management_service.py -k 'poll or apply or unauthorized' -x` | ❌ W0 | ⬜ pending |
| 09-02-02 | 02 | 2 | RMGT-02 | integration | `pytest tests/test_remote_management_service.py -k 'ack or applied or failed' -x` | ❌ W0 | ⬜ pending |
| 09-03-01 | 03 | 3 | RMGT-03 | unit | `pytest tests/test_remote_management_audit.py -k 'expired or idempotent' -x` | ❌ W0 | ⬜ pending |
| 09-03-02 | 03 | 3 | RMGT-03 | component | `npm --prefix console run test -- --run src/components/deployments/remote-action-card.test.tsx` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_remote_management_api.py` — admin queueing/history coverage for RMGT-01
- [ ] `tests/test_remote_management_service.py` — gateway poll/apply/ack and local authorization coverage for RMGT-02
- [ ] `tests/test_remote_management_audit.py` — TTL, duplicate suppression, and failure-reason coverage for RMGT-03
- [ ] `console/src/components/deployments/remote-action-card.test.tsx` — drawer action gating and confirmation behavior
- [ ] `console/src/lib/admin-api.remote-actions.test.ts` — deployment action client methods and duplicate-return behavior

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Confirm the hosted drawer copy clearly communicates that the action rotates only the hosted-link credential and does not affect serving traffic | RMGT-01 | Copy clarity is product-facing and easier to verify visually in the real drawer | Start gateway + console, open a linked deployment detail drawer, inspect the action card and confirmation copy, and confirm the wording mentions hosted-link credential scope and non-serving impact |
| Validate the end-to-end credential-rotation handshake against a running app pair using real polling timing | RMGT-02 | Timing-sensitive integration is best smoke-tested once outside the ASGI transport harness | Queue the action from the deployment drawer, watch the gateway logs and hosted history update, and confirm the deployment continues polling successfully after the rotation |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
