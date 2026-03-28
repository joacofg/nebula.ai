---
estimated_steps: 1
estimated_files: 5
skills_used: []
---

# T03: Add preview-before-save simulation to the policy editor

Extend `console/src/lib/admin-api.ts` with typed simulation request/response shapes and a client helper for the new admin endpoint. Update `console/src/app/(console)/policy/page.tsx` to own a simulation mutation alongside the existing save mutation, keeping draft preview and persistence separate. In `console/src/components/policy/policy-form.tsx`, add a simulate action that reuses the current draft-to-policy serialization, renders loading/error state, and shows the returned aggregate delta plus a compact changed-request summary without implying that anything was saved. Add/extend `console/src/components/policy/policy-form.test.tsx` and `console/src/components/policy/policy-page.test.tsx` so they prove draft values are sent to simulation, preview results render without saving, save remains explicit, and empty/error states are legible.

## Inputs

- ``console/src/lib/admin-api.ts``
- ``console/src/app/(console)/policy/page.tsx``
- ``console/src/components/policy/policy-form.tsx``
- ``console/src/components/policy/policy-form.test.tsx``
- ``console/src/components/policy/policy-page.test.tsx``

## Expected Output

- ``console/src/lib/admin-api.ts``
- ``console/src/app/(console)/policy/page.tsx``
- ``console/src/components/policy/policy-form.tsx``
- ``console/src/components/policy/policy-form.test.tsx``
- ``console/src/components/policy/policy-page.test.tsx``

## Verification

npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx

## Observability Impact

- Signals added/changed: inline preview state for loading, error, zero-result, and changed-outcome summaries.
- How a future agent inspects this: run the focused Vitest files and inspect the policy-page preview panel behavior.
- Failure state exposed: simulate-call errors and empty replay windows should render explicit UI feedback instead of looking like a successful save.
