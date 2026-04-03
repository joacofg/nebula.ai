# S04: Rework policy preview into a comparison-and-decision flow — UAT

**Milestone:** M007
**Written:** 2026-04-03T02:49:48.794Z

# S04: Rework policy preview into a comparison-and-decision flow — UAT

**Milestone:** M007
**Written:** 2026-04-01

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: This slice changes bounded console composition and mutation framing rather than backend runtime behavior. The decisive proof is the assembled page behavior locked by focused Vitest coverage at the form seam and the real policy page entrypoint.

## Preconditions

- `console/node_modules` is installed so Vitest can run.
- The worktree includes the S04 policy form and policy page changes.
- The tester can run focused console tests from the repo root.

## Smoke Test

Run:

`npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`

**Expected:** Both test files pass, proving the compare-before-save policy flow, explicit preview-only wording, bounded changed-request evidence, and stale-preview reset behavior after tenant switches and saves.

## Test Cases

### 1. Preview leads with a decision summary before supporting replay evidence

1. Run `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx`.
2. Inspect the passing assertions around the `Preview before save` section.
3. **Expected:** The preview shows a decision badge, preview-only/save-stays-separate wording, a baseline-versus-draft consequence summary, and explicit next-step guidance before the `Changed request sample` block appears.
4. **Expected:** Supporting replay evidence stays subordinate and bounded; the sample explains that it is a limited set of persisted requests whose route, status, policy outcome, or projected cost changed.

### 2. Preview remains explicitly non-saving across changed, unchanged, and empty-window states

1. Run `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`.
2. Review the assertions for changed previews, unchanged previews, and zero-row preview windows.
3. **Expected:** Changed previews still say `Preview only — save stays separate` and `This preview did not save the policy.`
4. **Expected:** Unchanged previews surface `No decision pressure` plus guidance to save only if the unchanged replay matches operator intent.
5. **Expected:** Zero-row previews surface `No comparison window` and explain that no recent traffic matched the replay window rather than implying a saved or failed change.

### 3. Null and rollout-disabled routing parity remain legible in the changed-request sample

1. Run `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`.
2. Inspect the passing assertions around malformed/null route fields and rollout-disabled parity.
3. **Expected:** Rows with null route mode/score still render readable parity strings such as `rollout disabled` or `unscored (degraded)` rather than crashing or hiding the row.
4. **Expected:** Route parity remains supporting evidence only and does not replace the main decision summary.

### 4. The real policy page keeps preview and save as separate mutations

1. Run `npm --prefix console run test -- --run src/components/policy/policy-page.test.tsx`.
2. Inspect the assertions around `Preview impact` and `Save policy`.
3. **Expected:** Preview calls `simulateTenantPolicy` with the current draft and the bounded payload shape (`limit: 50`, `changed_sample_limit: 5`) and does not call `updateTenantPolicy`.
4. **Expected:** The page intro frames the route as loading a tenant policy, comparing the baseline against a candidate draft using recent persisted traffic, and saving explicitly only after preview evidence supports the change.

### 5. Tenant changes and save success clear stale preview evidence

1. Run `npm --prefix console run test -- --run src/components/policy/policy-page.test.tsx`.
2. Review the passing assertions for `clears stale preview evidence after a successful save` and `clears stale preview evidence when switching tenants`.
3. **Expected:** After a preview has rendered changed-request evidence, a successful save removes that stale preview and returns the section to the neutral `Run a preview...` state.
4. **Expected:** Switching from Tenant A to Tenant B also clears the old preview sample before the new tenant policy loads, so prior comparison evidence does not leak across tenant contexts.

## Edge Cases

### Preview failure remains isolated from save

1. Run `npm --prefix console run test -- --run src/components/policy/policy-page.test.tsx`.
2. Review the `shows preview errors from the simulation mutation` case.
3. **Expected:** A simulation error renders `Preview failed: ...` inside the preview surface, save is not triggered, and the page does not drift into dashboard, routing-studio, or analytics language.

### No decision drift into dashboard framing

1. Run `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`.
2. Review the negative assertions in both suites.
3. **Expected:** The policy surface does not render language like `dashboard`, `routing studio`, or `analytics product`; the page remains a bounded compare-before-save decision tool.

## Failure Signals

- `policy-form.test.tsx` fails because the changed-request sample appears before the decision summary, preview-only wording disappears, or null parity rows crash.
- `policy-page.test.tsx` fails because the simulate payload shape changes, preview starts implying persistence, or stale preview evidence survives a tenant switch or successful save.
- Negative wording assertions fail, indicating page-identity drift toward dashboard or analytics framing.

## Requirements Proved By This UAT

- R049 — The operator decision-surface refinement remains bounded and interpretable instead of widening Nebula into an analytics-style dashboard or broader product sprawl.

## Not Proven By This UAT

- This UAT does not prove the integrated cross-surface handoff between Observability and policy decision flow; that belongs to S05 close-out.
- This UAT does not exercise live backend simulation behavior beyond the bounded request/response contracts already modeled in the focused page tests.

## Notes for Tester

If a failure involves repeated labels or supporting evidence text, first verify whether the regression is real page-hierarchy drift or only a test-scoping issue. In this slice, repeated supporting fields are acceptable as long as the decision summary stays primary, preview stays explicitly non-saving, and stale preview evidence never leaks across tenants or after save.
