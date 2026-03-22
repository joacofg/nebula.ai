---
phase: 8
slug: fleet-inventory-and-freshness-visibility
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend) + vitest (console) |
| **Config file** | `pyproject.toml` / `console/vitest.config.ts` |
| **Quick run command** | `pytest tests/test_heartbeat_api.py tests/test_freshness.py -x` |
| **Full suite command** | `make test && make console-test` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_heartbeat_api.py tests/test_freshness.py -x`
- **After every plan wave:** Run `make test && make console-test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | INVT-01 | integration | `pytest tests/test_heartbeat_api.py::test_heartbeat_updates_last_seen_at -x` | ❌ W0 | ⬜ pending |
| 08-01-02 | 01 | 1 | INVT-04 | integration | `pytest tests/test_heartbeat_api.py::test_heartbeat_updates_capability_flags -x` | ❌ W0 | ⬜ pending |
| 08-01-03 | 01 | 1 | INVT-02 | unit | `pytest tests/test_freshness.py -x` | ❌ W0 | ⬜ pending |
| 08-02-01 | 02 | 2 | INVT-01 | unit (vitest) | `npm --prefix console run test -- --run src/components/deployments/deployment-table.test.tsx` | ❌ W0 | ⬜ pending |
| 08-02-02 | 02 | 2 | INVT-02 | unit (vitest) | `npm --prefix console run test -- --run src/components/deployments/freshness-badge.test.tsx` | ❌ W0 | ⬜ pending |
| 08-03-01 | 03 | 2 | INVT-02 | unit | `pytest tests/test_freshness.py::test_freshness_reason_format -x` | ❌ W0 | ⬜ pending |
| 08-03-02 | 03 | 2 | INVT-04 | unit (vitest) | `npm --prefix console run test -- --run src/components/deployments/freshness-badge.test.tsx` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_heartbeat_api.py` — heartbeat ingest, last_seen_at update, capability flag persistence (INVT-01, INVT-04)
- [ ] `tests/test_freshness.py` — freshness calculation thresholds, reason code format (INVT-02)
- [ ] `console/src/components/deployments/freshness-badge.test.tsx` — freshness badge rendering per status (INVT-02, INVT-04)
- [ ] `console/src/components/deployments/deployment-table.test.tsx` — extend existing for new columns (INVT-01)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Stale/offline rows visually dimmed in fleet table | INVT-02 | CSS visual verification | Load fleet table with stale deployment; verify dimmed row styling |
| Dependency health pills render correct colors | INVT-01 | CSS color verification | View deployment detail with mixed dependency health; verify green/yellow/red pill colors |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
