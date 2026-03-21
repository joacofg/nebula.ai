---
phase: 7
slug: deployment-enrollment-and-identity
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-21
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x + pytest-asyncio (auto mode) |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/test_enrollment_api.py tests/test_gateway_enrollment.py -x` |
| **Full suite command** | `make test` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_enrollment_api.py tests/test_gateway_enrollment.py -x`
- **After every plan wave:** Run `make test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | ENRL-01 | integration | `pytest tests/test_enrollment_api.py::test_create_deployment_slot -x` | ❌ W0 | ⬜ pending |
| 07-01-02 | 01 | 1 | ENRL-01 | integration | `pytest tests/test_enrollment_api.py::test_list_deployments_includes_all_states -x` | ❌ W0 | ⬜ pending |
| 07-02-01 | 02 | 2 | ENRL-02 | integration | `pytest tests/test_enrollment_api.py::test_enrollment_exchange_success -x` | ❌ W0 | ⬜ pending |
| 07-02-02 | 02 | 2 | ENRL-02 | integration | `pytest tests/test_enrollment_api.py::test_enrollment_exchange_expired_token -x` | ❌ W0 | ⬜ pending |
| 07-02-03 | 02 | 2 | ENRL-02 | integration | `pytest tests/test_enrollment_api.py::test_enrollment_exchange_consumed_token -x` | ❌ W0 | ⬜ pending |
| 07-02-04 | 02 | 2 | ENRL-02 | integration | `pytest tests/test_gateway_enrollment.py::test_startup_enrollment_exchange -x` | ❌ W0 | ⬜ pending |
| 07-02-05 | 02 | 2 | ENRL-02 | integration | `pytest tests/test_gateway_enrollment.py::test_startup_no_token_skips_enrollment -x` | ❌ W0 | ⬜ pending |
| 07-02-06 | 02 | 2 | ENRL-02 | integration | `pytest tests/test_gateway_enrollment.py::test_startup_enrollment_failure_nonfatal -x` | ❌ W0 | ⬜ pending |
| 07-03-01 | 03 | 3 | ENRL-03 | integration | `pytest tests/test_enrollment_api.py::test_revoke_deployment -x` | ❌ W0 | ⬜ pending |
| 07-03-02 | 03 | 3 | ENRL-03 | integration | `pytest tests/test_enrollment_api.py::test_unlink_deployment -x` | ❌ W0 | ⬜ pending |
| 07-03-03 | 03 | 3 | ENRL-03 | integration | `pytest tests/test_enrollment_api.py::test_relink_preserves_single_record -x` | ❌ W0 | ⬜ pending |
| 07-03-04 | 03 | 3 | ENRL-03 | integration | `pytest tests/test_enrollment_api.py::test_list_includes_revoked_and_unlinked -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_enrollment_api.py` — stubs for ENRL-01, ENRL-02 (exchange), ENRL-03 (revoke/unlink/relink)
- [ ] `tests/test_gateway_enrollment.py` — stubs for ENRL-02 (gateway-side startup enrollment)
- [ ] `migrations/versions/20260321_0002_deployments.py` — `deployments` + `enrollment_tokens` tables

*Existing `configured_app` in `tests/support.py` covers test DB setup — new tests use it without modification.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Console UI copy-paste of enrollment token | ENRL-01 | Browser clipboard interaction | 1. Create deployment slot in console 2. Verify token displayed once 3. Verify copy button works |
| D-06 env warning after enrollment | ENRL-02 | Requires restart with stale env | 1. Set NEBULA_ENROLLMENT_TOKEN 2. Start gateway 3. Leave token in env 4. Restart gateway 5. Check logs for warning |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
