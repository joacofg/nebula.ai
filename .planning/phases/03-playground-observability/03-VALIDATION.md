---
phase: 3
slug: playground-observability
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-16
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest 8.x` + `Vitest 3.0.8` + `Playwright 1.51.0` |
| **Config file** | `pyproject.toml`, `console/vitest.config.ts`, `console/playwright.config.ts` |
| **Quick run command** | `./.venv/bin/pytest tests/test_governance_api.py tests/test_response_headers.py tests/test_health.py -q` |
| **Full suite command** | `make test && npm --prefix console run test -- --run && npm --prefix console run e2e` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `./.venv/bin/pytest tests/test_governance_api.py tests/test_response_headers.py tests/test_health.py -q`
- **After every plan wave:** Run `make test && npm --prefix console run test -- --run`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | PLAY-01 | backend integration | `./.venv/bin/pytest tests/test_admin_playground_api.py -q` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | PLAY-01 | browser e2e | `npm --prefix console run e2e -- playground.spec.ts` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 2 | PLAY-02 | backend integration | `./.venv/bin/pytest tests/test_admin_playground_api.py -q` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 2 | PLAY-02 | component | `npm --prefix console run test -- --run playground` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 2 | OBS-01 | backend integration | `./.venv/bin/pytest tests/test_governance_api.py -q` | ✅ | ⬜ pending |
| 03-03-02 | 03 | 2 | OBS-01 | browser e2e | `npm --prefix console run e2e -- observability.spec.ts` | ❌ W0 | ⬜ pending |
| 03-03-03 | 03 | 2 | OBS-02 | backend integration | `./.venv/bin/pytest tests/test_health.py -q` | ✅ | ⬜ pending |
| 03-03-04 | 03 | 2 | OBS-02 | component | `npm --prefix console run test -- --run health` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_admin_playground_api.py` — covers admin playground execution, request-id lookup/filtering, and header/ledger correlation
- [ ] `tests/test_health.py` extension or `tests/test_runtime_health.py` — covers premium-provider health status and degraded-state payloads
- [ ] `console/src/components/playground/*.test.tsx` — covers request form, result metadata panel, and recorded-outcome follow-up state
- [ ] `console/src/components/ledger/*.test.tsx` — covers tenant/status/time filters and empty/error states
- [ ] `console/src/components/health/*.test.tsx` — covers ready/degraded/not-ready card rendering
- [ ] `console/e2e/playground.spec.ts` — covers playground submit flow
- [ ] `console/e2e/observability.spec.ts` — covers ledger filters and dependency health display

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Playground response metadata and ledger follow-up remain visually coherent for an operator | PLAY-01, PLAY-02 | The critical behavior is the handoff between immediate response metadata and recorded ledger enrichment, which is hard to fully validate from static DOM assertions alone | Start the console, sign in, run a playground request for a known tenant, confirm the response panel shows route/provider/cache/fallback/policy values immediately, then confirm the recorded outcome section fills in request ID, terminal status, token totals, and estimated cost from the correlated ledger row |
| Dependency health view communicates degraded optional services without implying a hard outage | OBS-02 | Operators need to interpret mixed ready/degraded states accurately, and that wording/design quality is partly UX judgment | Start the app with one optional dependency degraded, open the health view, and confirm cache/local/premium provider cards clearly distinguish `ready`, `degraded`, and `not_ready` while preserving the overall gateway availability message |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
