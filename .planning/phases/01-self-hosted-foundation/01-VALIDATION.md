---
phase: 1
slug: self-hosted-foundation
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-15
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `./.venv/bin/pytest tests/test_settings.py tests/test_health.py -q` |
| **Full suite command** | `./.venv/bin/pytest -q` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `./.venv/bin/pytest tests/test_settings.py tests/test_health.py -q`
- **After every plan wave:** Run `./.venv/bin/pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | PLAT-01 | integration | `docker compose -f docker-compose.selfhosted.yml config` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | PLAT-01 | docs | `rg -n "docker compose -f docker-compose.selfhosted.yml up -d" README.md docs/self-hosting.md` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | PLAT-01 | command surface | `rg -n "^selfhost-(up|down|logs):" Makefile` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 2 | PLAT-02 | unit | `./.venv/bin/pytest tests/test_settings.py -q` | ✅ | ⬜ pending |
| 01-02-02 | 02 | 2 | PLAT-04 | api | `./.venv/bin/pytest tests/test_health.py -q` | ✅ | ⬜ pending |
| 01-02-03 | 02 | 2 | PLAT-04 | docs | `rg -n "/health/ready|/health/dependencies|premium_first" docs/self-hosting.md README.md deploy/selfhosted.env.example` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 3 | PLAT-03 | migration | `./.venv/bin/alembic upgrade head` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 3 | PLAT-03 | integration | `./.venv/bin/pytest tests/test_governance_api.py -q` | ✅ | ⬜ pending |
| 01-03-03 | 03 | 3 | PLAT-01 | deploy | `rg -n "alembic upgrade head|NEBULA_DATABASE_URL|postgresql\\+psycopg" Makefile docs/self-hosting.md docker-compose.selfhosted.yml deploy/selfhosted.env.example` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `docs/self-hosting.md` — operator deployment runbook for the canonical compose path
- [ ] `deploy/selfhosted.env.example` — self-hosted environment template separate from local dev defaults
- [ ] `tests/test_health.py` — readiness and degraded-dependency scenarios
- [ ] Alembic CLI availability via `pyproject.toml` dev/runtime dependencies

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Fresh self-hosted bring-up with a real premium provider key | PLAT-01, PLAT-02 | Requires an external upstream API key and a Docker-capable host | Copy `deploy/selfhosted.env.example` to a real env file, fill `NEBULA_PREMIUM_API_KEY`, run `docker compose -f docker-compose.selfhosted.yml up -d`, then confirm `/health`, `/health/ready`, and `/health/dependencies` from the running stack |
| Degraded local optimization while premium-first traffic remains available | PLAT-04 | Requires intentionally leaving Ollama offline while the rest of the stack is live | Start the self-hosted stack without Ollama, call `/health/dependencies`, and confirm `local_ollama` is degraded while `governance_store` remains ready and the app still serves traffic |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-15
