---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T02: Write the bounded M010 recovery proof walkthrough

Why: S04 must leave behind an operator-usable, pointer-first recovery proof path that tells reviewers exactly how to inspect outage evidence, perform recovery confirmation, and verify post-recovery truth without widening the product. Do: create `docs/m010-recovery-proof.md` modeled on the pointer-first structure of `docs/m009-integrated-proof.md`, anchored to existing `/health/ready`, `/health/dependencies`, and console Observability/runtime-health seams plus the new deterministic recovery tests from T01. Include canonical sources, minimal proof order, what counts as recovery confirmation, anti-goals around new dashboards and hosted authority, and a concise failure-mode section that makes drift obvious. Keep hosted/control-plane wording subordinate to `docs/hosted-reinforcement-boundary.md`. Done when: the doc is non-empty, references the current recovery-proof seams, and can guide a reviewer from outage truth through recovered behavior and operator-visible evidence using only existing surfaces.

## Inputs

- `docs/m009-integrated-proof.md`
- `docs/hosted-reinforcement-boundary.md`
- `tests/test_phase10_outage_safety.py`
- `tests/test_health.py`
- `console/src/components/health/runtime-health-cards.tsx`
- `console/src/app/(console)/observability/page.tsx`
- `console/src/lib/admin-api.ts`
- `.gsd/milestones/M010/M010-CONTEXT.md`
- `.gsd/milestones/M010/slices/S04/S04-RESEARCH.md`

## Expected Output

- `docs/m010-recovery-proof.md`

## Verification

python3 -c "from pathlib import Path; p = Path('docs/m010-recovery-proof.md'); assert p.exists() and p.stat().st_size > 0"

## Observability Impact

Documents the canonical operator inspection path for failure and recovery on already-shipped surfaces, improving human and agent diagnosability without adding a new UI or API.
