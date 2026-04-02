---
estimated_steps: 6
estimated_files: 3
skills_used: []
---

# T03: Render compact routing parity cues in the existing policy preview

Expose the new parity fields in the existing policy preview UI without widening it into a routing dashboard. Executors should keep the rendering compact and operator-readable so S03 stays bounded and S04 can build richer inspection later.

Steps:
1. Update `console/src/components/policy/policy-form.tsx` to render a concise parity line in each changed-request card using the new baseline/simulated route mode, calibrated/degraded markers, and route score fields when present.
2. Preserve explicit gated semantics: when route mode is null because calibrated routing is disabled, render the absence as an intentional gated state tied to the existing `calibrated_routing_disabled` reason rather than as missing data.
3. Keep the existing changed-request sample compact and reuse the established route vocabulary; do not add new sections, charts, or analytics framing.
4. Extend `console/src/components/policy/policy-page.test.tsx` to lock the parity rendering so future slices cannot regress the bounded preview contract.

## Inputs

- `console/src/components/policy/policy-form.tsx`
- `console/src/components/policy/policy-page.test.tsx`
- `console/src/lib/admin-api.ts`

## Expected Output

- `console/src/components/policy/policy-form.tsx`
- `console/src/components/policy/policy-page.test.tsx`

## Verification

npm --prefix console run test -- --run src/components/policy/policy-page.test.tsx

## Observability Impact

Improves operator-facing replay inspection in the existing preview panel by surfacing route-mode and degraded/gated state explicitly, while keeping the UI bounded and readable.
