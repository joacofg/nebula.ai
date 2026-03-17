---
phase: 3
slug: playground-observability
status: partial
nyquist_compliant: false
wave_0_complete: true
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
| **Quick run command** | `./.venv/bin/pytest tests/test_admin_playground_api.py tests/test_governance_api.py tests/test_health.py -q && npm --prefix console run test -- --run playground-form playground-response playground-metadata playground-page playground-recorded-outcome ledger-filters ledger-table runtime-health-cards` |
| **Full suite command** | `make test && npm --prefix console run test -- --run && npm --prefix console run e2e` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `./.venv/bin/pytest tests/test_admin_playground_api.py tests/test_governance_api.py tests/test_health.py -q`
- **After every plan wave:** Run `make test && npm --prefix console run test -- --run`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | PLAY-01 | backend integration | `./.venv/bin/pytest tests/test_admin_playground_api.py -q` | ✅ | ✅ green |
| 03-01-02 | 01 | 1 | PLAY-01 | browser e2e | `npm --prefix console run e2e -- playground.spec.ts` | ✅ | ❌ red |
| 03-02-01 | 02 | 2 | PLAY-02 | backend integration | `./.venv/bin/pytest tests/test_admin_playground_api.py -q` | ✅ | ✅ green |
| 03-02-02 | 02 | 2 | PLAY-02 | component | `npm --prefix console run test -- --run playground-form playground-response playground-metadata playground-page playground-recorded-outcome` | ✅ | ✅ green |
| 03-03-01 | 03 | 2 | OBS-01 | backend integration | `./.venv/bin/pytest tests/test_governance_api.py -q` | ✅ | ✅ green |
| 03-03-02 | 03 | 2 | OBS-01 | browser e2e | `npm --prefix console run e2e -- observability.spec.ts` | ✅ | ✅ green |
| 03-03-03 | 03 | 2 | OBS-02 | backend integration | `./.venv/bin/pytest tests/test_health.py -q` | ✅ | ✅ green |
| 03-03-04 | 03 | 2 | OBS-02 | component | `npm --prefix console run test -- --run ledger-filters ledger-table runtime-health-cards` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_admin_playground_api.py` — covers admin playground execution, request-id lookup/filtering, and header/ledger correlation
- [x] `tests/test_health.py` extension or `tests/test_runtime_health.py` — covers premium-provider health status and degraded-state payloads
- [x] `console/src/components/playground/*.test.tsx` — covers request form, result metadata panel, and recorded-outcome follow-up state
- [x] `console/src/components/ledger/*.test.tsx` — covers tenant/status/time filters and empty/error states
- [x] `console/src/components/health/*.test.tsx` — covers ready/degraded/not-ready card rendering
- [x] `console/e2e/playground.spec.ts` — test file exists; command is currently blocked by the Next.js build startup failure noted below
- [x] `console/e2e/observability.spec.ts` — covers ledger filters and dependency health display

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Playground response metadata and ledger follow-up remain visually coherent for an operator | PLAY-01, PLAY-02 | The critical behavior is the handoff between immediate response metadata and recorded ledger enrichment, which is hard to fully validate from static DOM assertions alone | Start the console, sign in, run a playground request for a known tenant, confirm the response panel shows route/provider/cache/fallback/policy values immediately, then confirm the recorded outcome section fills in request ID, terminal status, token totals, and estimated cost from the correlated ledger row |
| Dependency health view communicates degraded optional services without implying a hard outage | OBS-02 | Operators need to interpret mixed ready/degraded states accurately, and that wording/design quality is partly UX judgment | Start the app with one optional dependency degraded, open the health view, and confirm cache/local/premium provider cards clearly distinguish `ready`, `degraded`, and `not_ready` while preserving the overall gateway availability message |
| Playground browser journey from build-to-runtime remains executable under the Playwright web server | PLAY-01, PLAY-02 | `playwright.spec.ts` is currently blocked before the test starts because the Playwright web server build fails while renaming `.next/export/500.html` to `.next/server/pages/500.html` | From `console/`, run the Playwright web-server command path used by `console/playwright.config.ts`, confirm `npm run build && npm run start -- --hostname 127.0.0.1 --port 3001` starts cleanly, then rerun `npm --prefix console run e2e -- playground.spec.ts` |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** partial 2026-03-17

## Validation Audit 2026-03-17

| Metric | Count |
|--------|-------|
| Gaps found | 2 |
| Resolved | 1 |
| Escalated | 1 |

- Resolved: PLAY-02 component coverage was stale because two assertions still expected superseded recorded-outcome copy; both test files were updated and the focused Vitest command now passes.
- Escalated: `npm --prefix console run e2e -- playground.spec.ts` is blocked by a Playwright web-server startup failure during the Next.js build step: `ENOENT` while renaming `.next/export/500.html` to `.next/server/pages/500.html`.
