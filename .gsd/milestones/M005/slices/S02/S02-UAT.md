# S02: Policy simulation loop — UAT

**Milestone:** M005
**Written:** 2026-03-28T03:20:03.141Z

# S02 UAT — Policy simulation loop

## Scope
Validate that an operator can preview a candidate policy change against recent tenant ledger traffic before saving it, and that the preview is explicitly non-mutating.

## Preconditions
- Nebula backend dependencies are available and the test environment can run focused pytest coverage.
- Console dependencies are installed so focused Vitest policy tests can run.
- The worktree includes the S02 backend, admin API, and console changes.

## Test Case 1 — Backend replay service reports route and cost deltas without mutation
1. Run `./.venv/bin/pytest tests/test_service_flows.py -k simulation -x`.
2. Confirm the simulation-focused tests pass.
3. Review the covered scenarios in the passing output and source expectations:
   - recent tenant-scoped ledger rows are replayed and can change route targets;
   - newly denied requests are counted;
   - tenant/window scoping and empty windows are handled;
   - keyword-based route-signal replay works;
   - simulation does not persist policy or usage changes.

**Expected outcome:** The test command exits 0 with 4 passing simulation-focused tests, establishing that replay uses persisted ledger evidence and remains non-mutating.

## Test Case 2 — Admin simulation endpoint previews tenant traffic without changing saved policy
1. Run `./.venv/bin/pytest tests/test_governance_api.py -k simulation -x`.
2. Confirm the admin API simulation tests pass.
3. Verify the scenarios covered by the passing tests:
   - `POST /v1/admin/tenants/{tenant_id}/policy/simulate` returns aggregate replay output for an existing tenant;
   - missing tenants return 404;
   - inverted time windows are rejected;
   - newly denied outcomes are surfaced;
   - unchanged and empty windows are explicit;
   - saved tenant policy remains unchanged after simulation calls.

**Expected outcome:** The test command exits 0 with 5 passing simulation-focused API tests, demonstrating the endpoint is tenant-scoped, validation-aware, and non-mutating.

## Test Case 3 — Console preview-before-save flow shows simulation results without saving
1. Run `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`.
2. Confirm the policy preview component and page tests pass.
3. Verify the covered UI behaviors from the passing suite:
   - draft policy values are sent to simulation;
   - preview results render aggregate counts, changed-request samples, and replay notes;
   - the UI explicitly says the preview did not save the policy and that save remains explicit;
   - preview errors are legible;
   - zero-result previews are explicit;
   - save is a separate action and is not triggered by preview.

**Expected outcome:** The test command exits 0 with all policy preview tests passing, showing the operator sees preview feedback without persistence side effects.

## Test Case 4 — Changed-request sample communicates more than route-target flips
1. Inspect `console/src/components/policy/policy-form.tsx` and the passing assertions in `console/src/components/policy/policy-form.test.tsx`.
2. Confirm each changed-request row can summarize route, status, policy outcome, and projected cost differences.
3. Confirm at least one tested sample shows a policy/status or cost delta, not just a route-target delta.

**Expected outcome:** The preview contract communicates why a request is considered changed, even when the key difference is denial or cost rather than only route-target movement.

## Edge Cases
- Empty replay window: preview reports that no recent traffic matched and does not imply failure.
- Unchanged replay window: preview reports zero changed requests explicitly.
- Invalid replay filters: admin endpoint rejects inverted timestamps with a clear validation error.
- Missing tenant: admin endpoint returns 404 rather than simulating against fallback state.
- Approximation boundary: preview surfaces replay notes explaining that raw prompt text is unavailable and route-signal reconstruction is used instead.

## Operational Readiness (Q8)
- **Health signal:** Focused simulation verification stays green across backend service, admin API, and console policy preview suites.
- **Failure signal:** Preview requests return explicit admin errors, simulation tests fail, or the console stops rendering aggregate replay results / changed-request summaries.
- **Recovery procedure:** Re-run the focused test trio above, inspect `PolicySimulationService`, the admin simulation route, and console preview state wiring, then restore the replay contract before widening roadmap scope.
- **Monitoring gaps:** There is no dedicated runtime metric or admin telemetry stream yet for simulation usage/failure volume; current evidence is primarily test-backed and UI/API contract based.

