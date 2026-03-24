---
estimated_steps: 5
estimated_files: 7
skills_used:
  - react-best-practices
  - test
---

# T03: Lock the day-1 value story with backend and console proof tests

**Slice:** S04 — Day-1 value proof surface
**Milestone:** M001

## Description

Convert the S04 story into executable proof so the docs and UI cannot drift away from the actual runtime evidence. This task should extend the focused backend, component, and end-to-end tests that already cover migration, Playground, and Observability, adding assertions for the exact route/fallback/policy/ledger signals that make Nebula visibly valuable on day 1. Keep all assertions aligned to the current runtime contract rather than broadening product promises.

## Steps

1. Extend the focused backend suites so the canonical public migration proof and admin correlation proof explicitly assert the day-1 evidence surfaces S04 depends on.
2. Update the Playground component tests so they verify the newly rendered immediate and recorded fields, including tenant, route reason, policy mode, route target, provider, fallback/cache status, and policy outcome where applicable.
3. Update the Playwright Playground and Observability specs so the end-to-end operator story proves immediate response evidence, persisted recorded outcome, and visible dependency degradation in one coherent flow.
4. Keep the assertions bound to existing response headers, usage-ledger rows, and console copy introduced in T01/T02; do not invent unsupported states or alternate adoption paths.
5. Run the planned pytest, Vitest, and Playwright subsets (or document environment gaps if toolchains are unavailable in the worktree).

## Must-Haves

- [ ] Backend tests still prove the canonical public request plus `X-Request-ID` → usage-ledger correlation pattern and explicitly cover the route/fallback/policy fields S04 relies on.
- [ ] Console component and e2e tests prove that Playground and Observability surface one consistent immediate-versus-persisted value story for operators.

## Verification

- `pytest tests/test_reference_migration.py tests/test_admin_playground_api.py tests/test_governance_api.py -q`
- `npm --prefix console run test -- --run playground && npm --prefix console run test -- --run observability`
- `npm --prefix console run e2e -- --grep "playground|observability"`

## Observability Impact

- Signals added/changed: executable assertions now pin the exact header, ledger, Playground, and Observability fields that communicate day-1 routing/policy/fallback value.
- How a future agent inspects this: run the focused pytest, Vitest, and Playwright commands listed above.
- Failure state exposed: drift between public headers, persisted ledger outcomes, or UI presentation becomes a direct test failure instead of a narrative mismatch.

## Inputs

- `tests/test_reference_migration.py` — canonical public migration proof to extend without changing the public contract.
- `tests/test_admin_playground_api.py` — admin Playground and request-id correlation seam.
- `tests/test_governance_api.py` — persisted ledger and policy/fallback coverage seam.
- `console/src/components/playground/playground-metadata.test.tsx` — immediate metadata component assertions to expand.
- `console/src/components/playground/playground-recorded-outcome.test.tsx` — recorded outcome component assertions to expand.
- `console/e2e/playground.spec.ts` — end-to-end Playground proof to align with the richer day-1 fields.
- `console/e2e/observability.spec.ts` — end-to-end Observability proof to align with the persisted explanation story.
- `.gsd/milestones/M001/slices/S04/tasks/T02-PLAN.md` — expected UI fields and narrative that tests must lock in.

## Expected Output

- `tests/test_reference_migration.py` — strengthened public adoption/value assertions.
- `tests/test_admin_playground_api.py` — strengthened admin correlation/value assertions.
- `tests/test_governance_api.py` — strengthened persisted route/fallback/policy assertions if needed.
- `console/src/components/playground/playground-metadata.test.tsx` — updated immediate metadata component coverage.
- `console/src/components/playground/playground-recorded-outcome.test.tsx` — updated recorded outcome component coverage.
- `console/e2e/playground.spec.ts` — updated end-to-end Playground day-1 value proof.
- `console/e2e/observability.spec.ts` — updated end-to-end Observability day-1 value proof.
