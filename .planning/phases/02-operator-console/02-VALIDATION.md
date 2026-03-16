---
phase: 2
slug: operator-console
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-16
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest 8.x` + `Vitest` + `Playwright` |
| **Config file** | `pyproject.toml`, `console/package.json`, `console/vitest.config.ts`, `console/playwright.config.ts` |
| **Quick run command** | `./.venv/bin/pytest tests/test_governance_api.py -q && npm --prefix console run test -- --run` |
| **Full suite command** | `./.venv/bin/pytest -q && npm --prefix console run lint && npm --prefix console run test -- --run && npm --prefix console run e2e` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `./.venv/bin/pytest tests/test_governance_api.py -q && npm --prefix console run test -- --run`
- **After every plan wave:** Run `./.venv/bin/pytest -q && npm --prefix console run lint && npm --prefix console run test -- --run`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | CONS-01 | static + lint | `npm --prefix console run lint` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | CONS-01 | component | `npm --prefix console run test -- --run admin-login-form admin-session-provider` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | CONS-01 | backend + deploy | `./.venv/bin/pytest tests/test_governance_api.py -q && docker compose -f docker-compose.selfhosted.yml config` | ✅ / ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | CONS-02 | component | `npm --prefix console run test -- --run tenants-page tenant-editor-drawer` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 2 | CONS-02 | e2e | `npm --prefix console run e2e -- tenants.spec.ts` | ❌ W0 | ⬜ pending |
| 02-02-03 | 02 | 2 | CONS-03 | e2e | `npm --prefix console run e2e -- api-keys.spec.ts` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 3 | CONS-04 | backend | `./.venv/bin/pytest tests/test_governance_api.py -q` | ✅ | ⬜ pending |
| 02-03-02 | 03 | 3 | CONS-04 | component | `npm --prefix console run test -- --run policy-page policy-form` | ❌ W0 | ⬜ pending |
| 02-03-03 | 03 | 3 | CONS-04 | e2e | `npm --prefix console run e2e -- policy.spec.ts` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `console/package.json` — scripts for `lint`, `test`, `e2e`, `dev`, and `build`
- [ ] `console/vitest.config.ts` — component/unit test runner configuration
- [ ] `console/playwright.config.ts` — browser workflow configuration
- [ ] `console/src/test/` or equivalent — shared rendering, router, and fetch-mocking utilities
- [ ] `console/.env.example` — local console runtime contract including `NEBULA_API_BASE_URL`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Browser refresh clears the admin session and sends the operator back to login | CONS-01 | The critical behavior is browser-memory persistence semantics rather than a single DOM assertion | Start the console, log in with a valid admin key, refresh the browser tab, and confirm the tenants view is replaced by the login screen with a prompt to enter the key again |
| Fresh self-hosted deployment exposes both the console and API with working proxy connectivity | CONS-01, CONS-02, CONS-03, CONS-04 | Requires a Docker-capable host running the full multi-service stack | Run `docker compose -f docker-compose.selfhosted.yml up -d`, open `http://localhost:3000`, sign in with the configured admin key, and confirm tenant, API key, and policy requests succeed without browser CORS errors |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-16
