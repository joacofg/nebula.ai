---
estimated_steps: 4
estimated_files: 6
skills_used:
  - react-best-practices
---

# T02: Reframe Playground and Observability as operator evidence surfaces

**Slice:** S01 — Operator structuring truth surface
**Milestone:** M002

## Description

Align the Playground and Observability console entrypoints with the canonical operator story already established in the docs and backend/admin contracts. Playground must read as an admin-only, non-streaming corroboration surface where the operator chooses a tenant context on purpose; Observability must read as the persisted ledger and dependency-health explanation surface for recorded request outcomes.

## Steps

1. Read `src/nebula/api/routes/admin.py`, `console/src/app/(console)/playground/page.tsx`, `console/src/components/playground/playground-form.tsx`, and `console/src/app/(console)/observability/page.tsx` to confirm the copy stays inside the real admin-only and non-streaming boundaries.
2. Update Playground page and form wording so operators understand they are running an admin-session corroboration request for a selected tenant, not following the public `POST /v1/chat/completions` migration path.
3. Update Observability page framing so the usage ledger is described as the persisted explanation surface for recorded request outcomes and dependency health is described as supporting runtime context, while preserving the current immediate-response and recorded-outcome separation elsewhere.
4. Extend `console/src/components/playground/playground-form.test.tsx` and `console/src/components/playground/playground-page.test.tsx`, and add `console/src/app/(console)/observability/page.test.tsx` if missing, to lock the operator-only, non-streaming, persisted-outcome framing into tests.

## Must-Haves

- [ ] Playground copy explicitly reinforces operator/admin context, selected tenant context, and non-streaming behavior without implying it is the public integration boundary.
- [ ] Observability copy explicitly reinforces persisted request outcomes plus dependency health as the operator inspection surface.
- [ ] The task preserves the immediate-response-versus-recorded-ledger distinction already present in the Playground flow.

## Verification

- `npm --prefix console run test -- --run src/components/playground/playground-form.test.tsx src/components/playground/playground-page.test.tsx src/app/(console)/observability/page.test.tsx`
- Manual review — `console/src/app/(console)/playground/page.tsx`, `console/src/components/playground/playground-form.tsx`, and `console/src/app/(console)/observability/page.tsx` no longer read like generic or public-path surfaces.

## Observability Impact

- Signals added/changed: no new runtime signals; copy clarifies the meaning of existing request id, route metadata, ledger records, and dependency-health states.
- How a future agent inspects this: read the updated console page copy and run the focused vitest files for Playground and Observability.
- Failure state exposed: wording drift that misstates trust boundary, tenant selection, or persisted-outcome role becomes a targeted test failure.

## Inputs

- `src/nebula/api/routes/admin.py` — admin-only Playground contract and non-streaming constraint
- `console/src/app/(console)/playground/page.tsx` — page-level Playground framing to update
- `console/src/components/playground/playground-form.tsx` — operator form guidance to update
- `console/src/app/(console)/observability/page.tsx` — Observability framing to update
- `console/src/components/playground/playground-form.test.tsx` — form-level truth-surface tests to extend
- `console/src/components/playground/playground-page.test.tsx` — page-level truth-surface tests to extend

## Expected Output

- `console/src/app/(console)/playground/page.tsx` — updated operator-only Playground framing
- `console/src/components/playground/playground-form.tsx` — updated selected-tenant and non-streaming guidance
- `console/src/app/(console)/observability/page.tsx` — updated persisted-outcome and dependency-health framing
- `console/src/components/playground/playground-form.test.tsx` — assertions for operator-only Playground guidance
- `console/src/components/playground/playground-page.test.tsx` — assertions preserving immediate-versus-recorded evidence framing
- `console/src/app/(console)/observability/page.test.tsx` — focused page test for persisted explanation and dependency-health framing
