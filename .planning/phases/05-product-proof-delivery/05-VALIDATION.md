---
phase: 5
slug: product-proof-delivery
status: ready
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-17
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest 8.x` + `Vitest 3.2.4` + `Playwright 1.58.2` |
| **Config file** | `pyproject.toml`, `console/vitest.config.ts`, `console/playwright.config.ts` |
| **Quick run command** | `./.venv/bin/pytest tests/test_benchmarking.py -x && npm --prefix console run e2e -- playground.spec.ts observability.spec.ts` |
| **Full suite command** | `make test && npm --prefix console run test -- --run && npm --prefix console run e2e` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `./.venv/bin/pytest tests/test_benchmarking.py -x` for benchmark/report changes and `npm --prefix console run test -- --run` for console-only copy/structure changes.
- **After every plan wave:** Run `./.venv/bin/pytest tests/test_benchmarking.py -x && npm --prefix console run e2e -- playground.spec.ts observability.spec.ts`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | EVAL-01, EVAL-02 | unit | `./.venv/bin/pytest tests/test_benchmarking.py -q` | ✅ | ⬜ pending |
| 05-01-02 | 01 | 1 | EVAL-01 | unit | `./.venv/bin/pytest tests/test_benchmarking.py -q` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 2 | DOCS-01 | shell/doc consistency | `test -f README.md && test -f docs/self-hosting.md && rg -n "Product proof|self-hosting|docker compose -f docker-compose.selfhosted.yml up -d|NEBULA_ADMIN_API_KEY" README.md docs/self-hosting.md` | ✅ | ⬜ pending |
| 05-02-02 | 02 | 2 | DOCS-01 | shell/doc consistency | `test -f docs/architecture.md && test -f docs/evaluation.md && test -f docs/demo-script.md && rg -n "Request flow|Qdrant|usage ledger|benchmark-demo|report.md|avoided cost|fallback|Observability" README.md docs/architecture.md docs/evaluation.md docs/demo-script.md` | ❌ W0 | ⬜ pending |
| 05-03-01 | 03 | 3 | DOCS-01 | shell/doc consistency | `test -f docs/pilot-checklist.md && rg -n "Playground|Observability|fallback|degraded" docs/pilot-checklist.md` | ❌ W0 | ⬜ pending |
| 05-03-02 | 03 | 3 | DOCS-01 | browser e2e | `npm --prefix console run e2e -- playground.spec.ts observability.spec.ts` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `benchmarks/v1/demo-scenarios.jsonl` — required for the live demo subset under `EVAL-01`
- [ ] Extend `tests/test_benchmarking.py` to lock summary-first report fields, canonical comparison-group framing, and demo-subset behavior
- [ ] `docs/architecture.md` — required for `DOCS-01`
- [ ] `docs/evaluation.md` — required for `DOCS-01`
- [ ] `docs/demo-script.md` — required for `DOCS-01`
- [ ] `docs/pilot-checklist.md` — required for repeatable pilot/demo packaging
- [ ] Add a lightweight docs existence/consistency check command or equivalent shell verification for `DOCS-01`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Benchmark artifact story reads as persuasive product proof instead of a developer log | EVAL-01, EVAL-02 | Assertions can prove fields exist, but not whether the top-line savings/fallback narrative is actually legible to a reviewer | Run `make benchmark`, open the generated `report.md`, and confirm the first screen answers what Nebula saved, how traffic routed, whether fallback occurred, and whether any expectations failed without requiring the raw table first |
| README and focused docs feel coherent for a first-time pilot evaluator | DOCS-01 | Shell checks prove file presence and markers, but not whether navigation and framing are understandable | Start at `README.md`, follow links to self-hosting, architecture, evaluation, and demo docs, and confirm there is one clear path for deployment, proof, and live walkthrough |
| Demo-critical console copy makes the immediate-versus-recorded distinction obvious | DOCS-01 | Browser tests can assert strings, but clarity of the explanation is still a human judgment | Run the console, execute a Playground request, and confirm the metadata panel reads as immediate response evidence while the recorded outcome panel clearly reads as the persisted ledger record for the same request |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
