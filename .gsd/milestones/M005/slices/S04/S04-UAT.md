# S04: Recommendations and cache controls — UAT

**Milestone:** M005
**Written:** 2026-03-28T04:14:55.645Z

# S04 UAT — Recommendations and cache controls

## Preconditions
- Nebula backend dependencies are available and the admin API is reachable.
- A tenant exists with recent usage-ledger activity, including at least one premium-routed request and one cache-related outcome in the recent window.
- An admin session is available for the console and admin API.
- The database has the semantic-cache tuning columns from migration `20260328_0008_cache_policy_controls`.

## Test Case 1 — Tenant-scoped recommendations endpoint returns bounded grounded guidance
1. Call `GET /v1/admin/tenants/{tenant_id}/recommendations` with a valid admin key for an existing tenant.
   - Expected: Response status is 200.
2. Inspect the JSON payload.
   - Expected: The response contains `tenant_id`, `generated_at`, `window_requests_evaluated`, `recommendations`, and `cache_summary`.
   - Expected: `recommendations` contains at most 3 cards and each card contains bounded `code`, `title`, `priority`, `category`, `summary`, `recommended_action`, and evidence rows.
   - Expected: `cache_summary.insights` contains at most 2 entries with runtime/cache evidence only.
3. Repeat the same request for a missing tenant ID.
   - Expected: Response status is 404 with `Tenant not found.`
4. Repeat the request without admin authorization.
   - Expected: Response is rejected by admin protection.

## Test Case 2 — Degraded cache health stays visible in recommendation evidence
1. Put the semantic cache dependency into a degraded/not-ready state in a controlled test environment.
2. Call `GET /v1/admin/tenants/{tenant_id}/recommendations` again.
   - Expected: `cache_summary.runtime_status` reflects the degraded state and `runtime_detail` explains the issue.
   - Expected: At least one cache insight or recommendation explicitly surfaces degraded cache runtime instead of hiding recommendation output.
3. Restore healthy cache runtime and call the endpoint again.
   - Expected: Runtime status and insight wording update accordingly without changing the endpoint shape.

## Test Case 3 — Observability renders grounded recommendation framing without implying autonomous optimization
1. Open the console Observability page as an admin and select the tenant used above.
   - Expected: The page loads persisted request evidence, recommendation summary cards, and cache-effectiveness context for that tenant.
2. Read the recommendation section header and supporting copy.
   - Expected: The wording states recommendations are derived from recent ledger-backed traffic plus supporting runtime context.
   - Expected: The wording explicitly avoids implying black-box optimization or autosave behavior.
3. Inspect one recommendation card.
   - Expected: The card shows a bounded title, summary, recommended action, and supporting evidence values only.
4. Inspect the cache summary panel.
   - Expected: It shows estimated hit rate, avoided premium cost, runtime status/detail, similarity threshold, and max entry age.

## Test Case 4 — Cache tuning stays in the existing policy preview/save flow
1. Open the tenant policy page in the console.
   - Expected: Semantic cache similarity threshold and max entry age appear under runtime-enforced controls, not in a separate cache-management area.
2. Change similarity threshold and max entry age, then click **Preview impact**.
   - Expected: The console runs a preview/simulation without saving the policy.
   - Expected: The UI states that save remains explicit.
3. Confirm the policy has not yet been persisted (for example by refreshing before saving or checking the last saved values).
   - Expected: The original saved values remain until **Save policy** is clicked.
4. Click **Save policy**.
   - Expected: The updated cache tuning fields persist as part of the tenant policy payload.

## Test Case 5 — Validation and bounded control semantics for cache tuning
1. In the policy page, set semantic cache similarity threshold to a value below 0 or above 1.
   - Expected: The form blocks preview/save and shows a validation error explaining the allowed 0–1 range.
2. Set semantic cache max entry age to a non-integer, 0, or a value above 720.
   - Expected: The form blocks preview/save and shows a validation error explaining the allowed whole-hour 1–720 range.
3. Re-enter valid values and preview again.
   - Expected: Preview succeeds and returns to normal save/preview semantics.

## Edge Cases
- Tenant has no recent ledger rows.
  - Expected: Recommendations endpoint still returns a valid bounded shape with `window_requests_evaluated = 0`; Observability shows no immediate recommendation cards rather than failing.
- Semantic cache is disabled in policy.
  - Expected: Cache summary and insight wording reflect the disabled state and any recommendation guidance stays descriptive rather than attempting autonomous reconfiguration.
- Cache runtime is degraded while policy tuning values are valid.
  - Expected: Observability and the API continue to surface degraded runtime evidence while preserving the ability to inspect and save explicit policy controls.

## Verification Evidence Used In Slice Close-Out
- `./.venv/bin/pytest tests/test_service_flows.py -k "recommendation or cache" -x`
- `./.venv/bin/pytest tests/test_governance_api.py -k "recommendation or cache" -x`
- `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx`
