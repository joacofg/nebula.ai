---
phase: S01
slug: adaptive-routing-model
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-26
---

# S01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest with pytest-asyncio (auto mode) |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/test_router_signals.py -x` |
| **Full suite command** | `make test` |
| **Console quick run** | `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx` |
| **Estimated runtime** | ~30 seconds (pytest), ~10 seconds (console unit) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_router_signals.py -x`
- **After every plan wave:** Run `make test`
- **Before verification:** Full suite must be green
- **Max feedback latency:** ~30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| S01-T01 | S01-PLAN | 1 | R039 | unit | `pytest tests/test_router_signals.py::test_route_decision_carries_signals -x` | ❌ W0 | ⬜ pending |
| S01-T01 | S01-PLAN | 1 | R039 | unit | `pytest tests/test_router_signals.py::test_token_count_signal_from_prompt -x` | ❌ W0 | ⬜ pending |
| S01-T01 | S01-PLAN | 1 | R039 | unit | `pytest tests/test_router_signals.py::test_budget_proximity_signal -x` | ❌ W0 | ⬜ pending |
| S01-T01 | S01-PLAN | 1 | R039 | unit | `pytest tests/test_router_signals.py::test_model_constraint_signal -x` | ❌ W0 | ⬜ pending |
| S01-T01 | S01-PLAN | 1 | R039 | unit | `pytest tests/test_router_signals.py::test_score_by_complexity_tier -x` | ❌ W0 | ⬜ pending |
| S01-T02 | S01-PLAN | 1 | R039 | integration | `pytest tests/test_router_signals.py::test_route_signals_persisted_in_ledger -x` | ❌ W0 | ⬜ pending |
| S01-T02 | S01-PLAN | 1 | R039 | integration | `pytest tests/test_router_signals.py::test_route_score_header -x` | ❌ W0 | ⬜ pending |
| S01-T03 | S01-PLAN | 2 | R039 | console unit | `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_router_signals.py` — new file with stubs for all R039 unit and integration tests (the test file does not yet exist)

*Console test file already exists at `console/src/components/ledger/ledger-request-detail.test.tsx` — only new test cases need to be added.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Observability drawer shows Route Decision section with plain-language labels | R039 | UI rendering requires visual inspection | Open a completed request in Observability, expand detail drawer, verify "Route Decision" section shows token count, complexity tier, and reason code with labels |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
