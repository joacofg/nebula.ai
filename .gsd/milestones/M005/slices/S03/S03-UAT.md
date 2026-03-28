# S03: Hard budget guardrails — UAT

**Milestone:** M005
**Written:** 2026-03-28T03:47:29.859Z

# S03 UAT — Hard budget guardrails

## Preconditions
- Nebula backend dependencies are available and the Python virtualenv plus console dependencies are installed.
- A tenant exists with a valid premium-capable policy and an operator can access admin policy editing plus usage ledger detail.
- The worktree includes the S03 changes introducing `hard_budget_limit_usd` and `hard_budget_enforcement` in policy editing, runtime evaluation, and ledger detail.

## Test Case 1 — Policy editor shows runtime-enforced hard guardrails separately from advisory soft budget
1. Open the tenant policy editor.
   - Expected: The form contains explicit hard cumulative budget inputs for the spend limit and enforcement mode.
2. Inspect the copy around the hard-budget controls.
   - Expected: The copy describes them as runtime-enforced controls that affect request behavior after the cumulative cap is exhausted.
3. Inspect the copy around `soft_budget_usd`.
   - Expected: `soft_budget_usd` remains described as advisory-only or soft-signal guidance, not an enforced cap.
4. Save a policy with `hard_budget_limit_usd` populated and enforcement set to downgrade-capable behavior.
   - Expected: The save succeeds and subsequent policy loads show the same hard-budget values without dropping them.

## Test Case 2 — Compatible auto-routed traffic downgrades to local after hard cap exhaustion
1. Configure a tenant policy with a low `hard_budget_limit_usd` that can be exceeded by recent premium usage and choose the downgrade-capable enforcement mode.
   - Expected: The policy persists and the tenant remains otherwise eligible for local routing.
2. Send or replay an auto-routed request whose route is compatible with local execution once the premium budget is exhausted.
   - Expected: The request is not ambiguously denied; it resolves to a local/downgraded outcome.
3. Open the corresponding usage-ledger request detail.
   - Expected: The detail shows a labeled hard-budget outcome explaining that the cumulative cap was exhausted and the request was downgraded to local.
4. Review the persisted policy outcome field and the structured budget evidence together.
   - Expected: Audit continuity is preserved through the raw `policy_outcome`, and the labeled evidence makes the downgrade understandable without reading raw JSON.

## Test Case 3 — Explicit premium request is denied when downgrade is impossible or disallowed
1. Configure or reuse a tenant whose cumulative premium spend already exceeds the hard budget cap.
   - Expected: The tenant is in a budget-exhausted state for premium requests.
2. Issue a request that explicitly requires premium behavior (for example an explicit premium route or premium-only request).
   - Expected: The request is denied rather than silently downgraded.
3. Inspect the policy outcome and request detail evidence.
   - Expected: The denial language states that the hard cumulative budget guardrail blocked premium usage and explains why downgrade could not occur.
4. Confirm soft-budget wording did not trigger the denial path.
   - Expected: The evidence references hard-budget enforcement, not advisory soft-budget guidance.

## Test Case 4 — Simulation preview matches runtime hard-budget semantics
1. Open the policy editor and prepare a candidate policy that adds or tightens `hard_budget_limit_usd` / `hard_budget_enforcement`.
   - Expected: The editor allows previewing the change before save.
2. Run policy simulation against recent tenant traffic.
   - Expected: The preview returns changed-request evidence and aggregate deltas without mutating the saved policy.
3. Inspect a changed request in the simulation output that crosses the hard-budget threshold.
   - Expected: The sample shows the same downgrade-versus-deny semantics used at runtime, including policy outcome and any premium-cost delta changes.
4. Save the candidate policy and compare a real subsequent runtime request in the same scenario.
   - Expected: Runtime behavior matches the simulation preview because both rely on the same `PolicyService.evaluate()` logic.

## Test Case 5 — Replay-window edge case uses prior spend only
1. Select a historical premium request near the guardrail threshold and run a simulation window that includes it.
   - Expected: The simulation processes requests chronologically oldest-first.
2. Inspect the simulated decision for that request.
   - Expected: The threshold calculation uses cumulative spend before the request (`before_timestamp` semantics), so the request does not count its own ledger row when determining exhaustion.
3. Compare the changed-request evidence ordering.
   - Expected: Samples appear in deterministic chronological order, consistent with the shared replay contract.

## Edge Cases
- Saving a policy that sets hard-budget fields must not erase them on subsequent admin reads or policy-editor reloads.
- A tenant with only advisory `soft_budget_usd` configured must continue operating without hard enforcement or denial.
- If a request remains on the same route target during simulation but policy outcome or projected premium cost changes, the request still counts as changed evidence.
- Operators should be able to understand hard-budget outcomes from labeled fields and docs without inferring semantics from raw strings or billing-specific dashboards.

