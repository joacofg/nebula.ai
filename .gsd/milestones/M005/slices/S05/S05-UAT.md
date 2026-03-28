# S05: Integrated v4 proof — UAT

**Milestone:** M005
**Written:** 2026-03-28T04:24:16.052Z

# S05 UAT — Integrated v4 proof

## Preconditions
- Worktree contains `docs/v4-integrated-proof.md`, `README.md`, and `docs/architecture.md` from S05.
- Python virtualenv dependencies are installed in `./.venv`.
- Console dependencies are installed under `console/node_modules`.
- Existing S02-S04 runtime and console surfaces are available in the worktree.

## Test Case 1 — Discover the integrated v4 proof from top-level docs
1. Open `README.md`.
   - Expected: the docs list includes a `v4 integrated proof` entry pointing to `docs/v4-integrated-proof.md`.
2. Open `docs/architecture.md`.
   - Expected: the architecture guide includes a pointer to `docs/v4-integrated-proof.md` alongside other canonical proof/contract references, without restating the full v4 contract inline.
3. Open `docs/v4-integrated-proof.md`.
   - Expected: the document exists, contains multiple second-level sections, and has no `TODO` or `TBD` markers.

## Test Case 2 — Follow the proof order and confirm scope discipline
1. Read the “What this integrated proof establishes” and “Canonical proof order” sections in `docs/v4-integrated-proof.md`.
   - Expected: the walkthrough explicitly orders the proof as route vocabulary -> policy replay -> hard/advisory budget distinction -> recommendations/cache posture -> Observability corroboration -> benchmark evidence.
2. Read the “What this walkthrough intentionally does not duplicate” section.
   - Expected: the doc states that detailed contracts remain in canonical docs/code surfaces and does not introduce new API, billing, analytics, SDK, or hosted-authority promises.
3. Read the “Failure modes this integrated proof makes obvious” section.
   - Expected: the doc explicitly flags scope drift such as autonomous optimization language, separate cache-management subsystems, or Observability becoming an authority surface.

## Test Case 3 — Reverify the backend/admin decisioning seams named by the walkthrough
1. Run `./.venv/bin/pytest tests/test_service_flows.py -k "simulation or recommendation or cache or runtime_policy or budget" -x`.
   - Expected: the focused service-flow suite passes, covering simulation replay, recommendation/cache behavior, runtime policy, and budget handling.
2. Run `./.venv/bin/pytest tests/test_governance_api.py -k "simulation or recommendation or guardrail or policy_options or policy_denied" -x`.
   - Expected: the focused governance API suite passes, covering simulation, recommendations, guardrails, policy options, and policy-denied outcomes.

## Test Case 4 — Reverify the console/operator proof surfaces named by the walkthrough
1. Run `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx`.
   - Expected: all targeted Vitest files pass.
2. Review the affected test names/output if needed.
   - Expected: coverage includes Observability wording, policy preview/save discipline, and ledger request-detail evidence rather than unrelated console areas.

## Edge Cases
- If `docs/v4-integrated-proof.md` exists but README or architecture stop linking to it, treat the slice as discoverability-regressed even if the runtime tests still pass.
- If the integrated proof starts restating detailed route/policy/recommendation contracts inline, treat that as scope drift even if the links still exist.
- If focused tests pass but the walkthrough changes the proof order to start with Observability or recommendation surfaces before route vocabulary and policy replay, treat that as a regression in the operator story.
- If a broader runner fails in unrelated untouched areas, do not use that alone as evidence that the v4 proof surfaces regressed; the targeted slice verification commands above are the acceptance gate.
