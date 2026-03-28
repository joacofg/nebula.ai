---
id: T02
parent: S05
milestone: M005
provides: []
requires: []
affects: []
key_files: ["README.md", "docs/architecture.md", ".gsd/milestones/M005/slices/S05/tasks/T02-SUMMARY.md"]
key_decisions: ["Kept discoverability wiring in existing top-level documentation surfaces and used explicit file/link checks in verification instead of adding a prose-snapshot documentation test."]
patterns_established: []
drill_down_paths: []
observability_surfaces: []
duration: ""
verification_result: "Ran the focused backend suite for simulation, recommendations, cache behavior, runtime policy, and budget handling; ran the focused admin API suite for simulation, recommendation, guardrail, policy options, and policy-denied behavior; ran the targeted console Vitest files for Observability, policy editing/preview, and ledger detail wording; then verified that docs/v4-integrated-proof.md exists and that both README.md and docs/architecture.md link to it."
completed_at: 2026-03-28T04:21:47.290Z
blocker_discovered: false
---

# T02: Added pointer-only README and architecture links for the v4 integrated proof and verified the end-to-end decisioning story across backend, admin API, console, and docs.

> Added pointer-only README and architecture links for the v4 integrated proof and verified the end-to-end decisioning story across backend, admin API, console, and docs.

## What Happened
---
id: T02
parent: S05
milestone: M005
key_files:
  - README.md
  - docs/architecture.md
  - .gsd/milestones/M005/slices/S05/tasks/T02-SUMMARY.md
key_decisions:
  - Kept discoverability wiring in existing top-level documentation surfaces and used explicit file/link checks in verification instead of adding a prose-snapshot documentation test.
duration: ""
verification_result: passed
completed_at: 2026-03-28T04:21:47.290Z
blocker_discovered: false
---

# T02: Added pointer-only README and architecture links for the v4 integrated proof and verified the end-to-end decisioning story across backend, admin API, console, and docs.

**Added pointer-only README and architecture links for the v4 integrated proof and verified the end-to-end decisioning story across backend, admin API, console, and docs.**

## What Happened

Updated README.md and docs/architecture.md to surface docs/v4-integrated-proof.md alongside the existing integrated-proof and contract references without restating the v4 contract details. Verified that the repository already had focused tests covering the runtime seams named in the task plan, so no new documentation test file was added; instead, discoverability was locked with explicit file and link checks in the verification chain. The resulting proof path is easier to find from top-level documentation while preserving the existing backend, admin API, and console evidence surfaces for simulation replay, hard guardrails, bounded recommendations, cache controls, and operator-facing wording.

## Verification

Ran the focused backend suite for simulation, recommendations, cache behavior, runtime policy, and budget handling; ran the focused admin API suite for simulation, recommendation, guardrail, policy options, and policy-denied behavior; ran the targeted console Vitest files for Observability, policy editing/preview, and ledger detail wording; then verified that docs/v4-integrated-proof.md exists and that both README.md and docs/architecture.md link to it.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_service_flows.py -k "simulation or recommendation or cache or runtime_policy or budget" -x` | 0 | ✅ pass | 1095ms |
| 2 | `./.venv/bin/pytest tests/test_governance_api.py -k "simulation or recommendation or guardrail or policy_options or policy_denied" -x` | 0 | ✅ pass | 17700ms |
| 3 | `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx` | 0 | ✅ pass | 1969ms |
| 4 | `test -f docs/v4-integrated-proof.md` | 0 | ✅ pass | 3ms |
| 5 | `rg -n "v4-integrated-proof\.md" README.md docs/architecture.md` | 0 | ✅ pass | 15ms |


## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `README.md`
- `docs/architecture.md`
- `.gsd/milestones/M005/slices/S05/tasks/T02-SUMMARY.md`


## Deviations
None.

## Known Issues
None.
