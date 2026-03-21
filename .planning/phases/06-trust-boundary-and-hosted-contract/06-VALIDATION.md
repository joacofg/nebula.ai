---
phase: 06
slug: trust-boundary-and-hosted-contract
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-21
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest` (`>=8.2.0,<9.0.0`), `vitest` (`^3.0.8`), `@playwright/test` (`^1.51.0`) |
| **Config file** | `pyproject.toml`, `console/vitest.config.ts`, `console/playwright.config.ts` |
| **Quick run command** | `pytest tests/test_hosted_contract.py -x && npm --prefix console run test -- --run trust-boundary` |
| **Full suite command** | `pytest && npm --prefix console run test && npm --prefix console run e2e` |
| **Estimated runtime** | ~90 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_hosted_contract.py -x` or `npm --prefix console run test -- --run trust-boundary`
- **After every plan wave:** Run `pytest && npm --prefix console run test`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | TRST-02 | unit | `pytest tests/test_hosted_contract.py -x` | ❌ W0 | ⬜ pending |
| 06-02-01 | 02 | 1 | TRST-01 | unit | `npm --prefix console run test -- --run trust-boundary-card` | ❌ W0 | ⬜ pending |
| 06-03-01 | 03 | 2 | TRST-01 | e2e | `npm --prefix console run e2e -- trust-boundary.spec.ts` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_hosted_contract.py` — schema drift and excluded-data assertions for TRST-02
- [ ] `console/src/components/hosted/trust-boundary-card.test.tsx` — disclosure copy and hosted-vs-local separation checks for TRST-01
- [ ] `console/src/app/trust-boundary/page.test.tsx` — public route rendering and excluded-data list coverage
- [ ] `console/e2e/trust-boundary.spec.ts` — route visibility and disclosure persistence before auth-gated surfaces

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Architecture and self-hosting docs use identical hosted/local authority language and exclusions as the contract model | TRST-01, TRST-02 | Final wording consistency across narrative docs is easier to assess in a targeted doc review than through a stable parser | Read `docs/architecture.md` and `docs/self-hosting.md`, confirm both explicitly say the hosted plane is not in the serving path, list the excluded data classes, and distinguish hosted freshness from locally authoritative runtime state |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
