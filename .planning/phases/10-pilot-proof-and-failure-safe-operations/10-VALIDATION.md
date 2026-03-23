---
phase: 10
slug: pilot-proof-and-failure-safe-operations
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest`, `pytest-asyncio`, `vitest` |
| **Config file** | `pyproject.toml`, `console/vitest.config.ts`, `console/playwright.config.ts` |
| **Quick run command** | `pytest tests/test_phase10_outage_safety.py -x` |
| **Full suite command** | `make test` and `make console-test` |
| **Estimated runtime** | ~90 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_phase10_outage_safety.py -x`
- **After every plan wave:** Run `make test` and `make console-test`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | INVT-03 | integration | `pytest tests/test_phase10_outage_safety.py -x` | ❌ W0 | ⬜ pending |
| 10-01-02 | 01 | 1 | INVT-03 | integration | `pytest tests/test_remote_management_service.py -k "hosted or outage or stale" -x` | ✅ | ⬜ pending |
| 10-02-01 | 02 | 2 | TRST-03 | unit | `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx` | ❌ W0 | ⬜ pending |
| 10-02-02 | 02 | 2 | TRST-03 | manual | `grep -n "hosted" docs/self-hosting.md docs/demo-script.md docs/pilot-checklist.md` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase10_outage_safety.py` — outage-safety integration coverage for INVT-03
- [ ] `console/src/app/trust-boundary/page.test.tsx` — trust-boundary copy regression coverage if page copy changes
- [ ] Existing infrastructure covers the remaining phase requirements

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Pilot docs explain onboarding, trust boundary, remote-management limits, and hosted outage behavior without overstating hosted authority | TRST-03 | The combined pilot narrative spans multiple docs and a demo flow, which automated tests cannot fully validate for accuracy and consistency | Review `docs/self-hosting.md`, `docs/demo-script.md`, and `docs/pilot-checklist.md`; confirm each states that hosted outage degrades visibility only, remote actions remain narrow and fail closed, and local serving stays authoritative |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
