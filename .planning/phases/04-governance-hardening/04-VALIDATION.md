---
phase: 4
slug: governance-hardening
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-16
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest 8.x` + `pytest-asyncio 0.23.x`; `vitest 3.x`; `@playwright/test 1.51.x` |
| **Config file** | `pyproject.toml`, `console/package.json` |
| **Quick run command** | `.venv/bin/pytest tests/test_governance_api.py tests/test_response_headers.py -q` |
| **Full suite command** | `.venv/bin/pytest && npm --prefix console run test -- --run` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/pytest tests/test_governance_api.py tests/test_response_headers.py -q`
- **After every plan wave:** Run `.venv/bin/pytest && npm --prefix console run test -- --run`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 25 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | GOV-01 | integration | `.venv/bin/pytest tests/test_governance_api.py tests/test_service_flows.py tests/test_governance_runtime_hardening.py -q` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 2 | GOV-02, ROUT-01 | integration | `.venv/bin/pytest tests/test_response_headers.py tests/test_service_flows.py tests/test_governance_runtime_hardening.py -q` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 2 | GOV-02, ROUT-01 | integration | `.venv/bin/pytest tests/test_governance_api.py tests/test_admin_playground_api.py tests/test_response_headers.py tests/test_governance_runtime_hardening.py -q` | ❌ W0 | ⬜ pending |
| 04-03-01 | 03 | 3 | GOV-01 | component | `npm --prefix console run test -- --run policy-form policy-page` | ✅ | ⬜ pending |
| 04-03-02 | 03 | 3 | GOV-01 | console/e2e | `npm --prefix console run e2e -- policy.spec.ts` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_governance_runtime_hardening.py` — add an end-to-end routing-mode matrix for `auto`, `local_only`, and `premium_only`, including explicit-model conflicts
- [ ] `tests/test_governance_api.py` — add inactive-tenant request cases and exact `detail` assertions
- [ ] `tests/test_response_headers.py` or a new denied-path test file — verify metadata exposure for `policy_denied` and fallback-disabled failures
- [ ] `tests/test_admin_playground_api.py` — add inactive-tenant playground coverage
- [ ] `console/src/components/policy/policy-form.test.tsx` and `console/src/components/policy/policy-page.test.tsx` — assert backend-driven runtime/advisory copy once `runtime_enforced_fields` and `advisory_fields` land
- [ ] `console/e2e/policy.spec.ts` — assert `Runtime-enforced controls` and the exact advisory copy while preserving the existing explicit-save flow

Wave 0 note: `tests/test_governance_runtime_hardening.py` does not exist yet in the workspace and is created by Plan `04-01` before any verify command that references it runs.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Operator can explain a denied or fallback-blocked request from the API response and ledger together | GOV-02, ROUT-01 | The key risk is semantic clarity across response detail, headers, and persisted ledger metadata, which is hard to fully judge from assertions alone | Trigger a denied premium-model request and a local-provider failure with fallback disabled, then confirm the API response and the correlated ledger row tell a consistent story about why the route was denied or why fallback did not occur |
| Policy editor wording stays aligned with backend-authoritative behavior if the visible contract changes | GOV-01 | UI copy can pass DOM assertions while still overstating what the runtime enforces | Open the console policy screen, inspect advanced controls, save a changed policy, and confirm every visible control is either enforced by runtime tests or clearly labeled as stored-only/advisory |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 25s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
