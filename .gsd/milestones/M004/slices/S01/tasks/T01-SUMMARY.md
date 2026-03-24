---
id: T01
parent: S01
milestone: M004
provides:
  - Canonical hosted reinforcement vocabulary and non-authority guardrails in the shared hosted contract seam
key_files:
  - console/src/lib/hosted-contract.ts
  - console/src/lib/hosted-contract.test.ts
  - .gsd/milestones/M004/slices/S01/tasks/T01-PLAN.md
  - .gsd/milestones/M004/slices/S01/S01-PLAN.md
key_decisions:
  - Kept reinforcement vocabulary in console/src/lib/hosted-contract.ts and enforced required phrases with a runtime assertion instead of creating another wording module
patterns_established:
  - Shared content modules can fail fast on both schema drift and vocabulary drift by asserting canonical phrases inside the exported content helper
observability_surfaces:
  - console/src/lib/hosted-contract.ts
  - console/src/lib/hosted-contract.test.ts
  - /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/pytest tests/test_hosted_contract.py -q
  - sh -lc 'cd console && npm run test -- --run src/lib/hosted-contract.test.ts'
duration: 33m
verification_result: passed
completed_at: 2026-03-24T11:23:00-03:00
blocker_discovered: false
---

# T01: Lock shared hosted reinforcement guardrails in the canonical content module

**Locked canonical hosted reinforcement guardrails in the shared contract module and added drift-failing tests for allowed claims, prohibited authority language, and bounded-action phrasing.**

## What Happened

I first fixed the task-plan observability gap by adding an `## Observability Impact` section to `.gsd/milestones/M004/slices/S01/tasks/T01-PLAN.md` so future agents can see where copy drift will surface.

Then I extended `console/src/lib/hosted-contract.ts` without widening the backend export contract. The module now exports a structured `reinforcementContract` covering allowed descriptive claims, prohibited authority implications, operator-reading guidance, and bounded-action phrasing. I kept this inside the existing schema-backed hosted contract seam and updated `getHostedContractContent()` to return it alongside the existing schema-derived exported-field data.

To make the seam fail fast on wording drift instead of only schema drift, I added `assertReinforcementContract()`. It checks for required phrases like metadata-backed/descriptive-only framing, fleet posture wording, request-serving-path guardrails, local runtime authority guardrails, and bounded credential-rotation phrasing before content is returned.

Finally, I expanded `console/src/lib/hosted-contract.test.ts` to lock the exact reinforcement arrays and bounded-action copy, while preserving the earlier schema-order, label, freshness, excluded-data, and copy-string assertions.

## Verification

I ran the task-level verification commands and then the slice-level verification commands.

- The frontend task-level test passed after installing console dependencies in the worktree with `sh -lc 'cd console && npm install ...'`; plain `npm --prefix console run test ...` initially failed because `vitest` was not available on PATH before that install.
- The backend task-level contract test passed unchanged, confirming no backend schema widening was introduced.
- The slice-level frontend and backend suites also passed at this intermediate stage.
- The slice grep check passed and showed the new wording in the canonical module/tests plus pre-existing slice surfaces.
- The slice `test -f docs/hosted-reinforcement-boundary.md` check failed, which is expected for T01 because that artifact is scheduled for T03.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts` | 127 | ❌ fail | ~1s |
| 2 | `pytest tests/test_hosted_contract.py -q` | 127 | ❌ fail | ~1s |
| 3 | `sh -lc 'cd console && npm install && npm run test -- --run src/lib/hosted-contract.test.ts'` | 0 | ✅ pass | ~8s |
| 4 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/pytest tests/test_hosted_contract.py -q` | 0 | ✅ pass | ~1s |
| 5 | `sh -lc 'cd console && npm run test -- --run src/lib/hosted-contract.test.ts src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx src/components/deployments/remote-action-card.test.tsx'` | 0 | ✅ pass | ~1s |
| 6 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q` | 0 | ✅ pass | ~2s |
| 7 | `rg -n "metadata-only|request-serving path|local runtime authority|serving traffic|tenant policy|provider credentials|fleet posture|confidence" console/src docs` | 0 | ✅ pass | <1s |
| 8 | `test -f docs/hosted-reinforcement-boundary.md` | 1 | ❌ fail | <1s |

## Diagnostics

Inspect `console/src/lib/hosted-contract.ts` for the canonical hosted reinforcement exports and the `assertReinforcementContract()` fail-fast logic. Inspect `console/src/lib/hosted-contract.test.ts` for the exact locked phrases that surface drift as focused Vitest failures. Backend alignment remains visible through `tests/test_hosted_contract.py`, which still passes against the committed schema artifact.

## Deviations

Used `sh -lc 'cd console && ...'` plus the repo-root venv pytest binary for verification because the worktree initially lacked local console `node_modules` and the plain `pytest`/`vitest` commands were unavailable on PATH. This changed execution mechanics only, not task scope or shipped behavior.

## Known Issues

`docs/hosted-reinforcement-boundary.md` does not exist yet, so the full slice artifact check still fails until T03 creates it.

## Files Created/Modified

- `console/src/lib/hosted-contract.ts` — added canonical reinforcement vocabulary, operator guidance, bounded-action phrasing, and fail-fast vocabulary assertions.
- `console/src/lib/hosted-contract.test.ts` — locked the new reinforcement exports and required non-authoritative phrases alongside existing schema/copy parity checks.
- `.gsd/milestones/M004/slices/S01/tasks/T01-PLAN.md` — added the missing `## Observability Impact` section required by the task pre-flight.
- `.gsd/milestones/M004/slices/S01/S01-PLAN.md` — marked T01 complete.
