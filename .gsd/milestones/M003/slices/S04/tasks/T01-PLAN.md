---
estimated_steps: 3
estimated_files: 4
skills_used:
  - test
---

# T01: Make embeddings ledger rows intentionally discoverable in Observability

**Slice:** S04 — Durable evidence correlation
**Milestone:** M003

## Description

Make the existing durable evidence path intentionally reachable from the operator UI. This task should keep the backend/admin API contract exactly as it is and instead fix the obvious operator-surface gap: Observability’s route-target filter currently does not recognize embeddings rows, even though the durable ledger truth already records `final_route_target="embeddings"`. The outcome should be a narrow UI update plus focused coverage proving that an operator can explicitly ask for embeddings rows.

## Steps

1. Read `console/src/components/ledger/ledger-filters.tsx`, `console/src/app/(console)/observability/page.tsx`, and `console/src/lib/admin-api.ts` to confirm the existing filter/query wiring and preserve the shared `routeTarget` → `route_target` admin API path.
2. Update the route-target options so embeddings is a first-class filter value, without introducing a new filter model, a new endpoint, or route-specific branching in the Observability page.
3. Extend `console/src/components/ledger/ledger-filters.test.tsx` to assert that the embeddings option is visible/selectable and that the existing callback path is used when an operator chooses it.

## Must-Haves

- [ ] `console/src/components/ledger/ledger-filters.tsx` includes an `embeddings` route-target option while preserving the shared usage-ledger filter contract.
- [ ] `console/src/components/ledger/ledger-filters.test.tsx` proves the operator can select embeddings filtering through the existing callback path.

## Verification

- `npm --prefix console run test -- --run src/components/ledger/ledger-filters.test.tsx`
- `rg -n 'embeddings' console/src/components/ledger/ledger-filters.tsx console/src/components/ledger/ledger-filters.test.tsx console/src/app/\(console\)/observability/page.tsx -S`

## Observability Impact

- Signals added/changed: the operator filter surface can now intentionally request usage-ledger rows whose durable route target is `embeddings`.
- How a future agent inspects this: open `console/src/components/ledger/ledger-filters.tsx` and run the focused Vitest file to confirm the UI still maps to the existing `routeTarget` filter path.
- Failure state exposed: if embeddings disappears from the filter set again, the focused test fails before later browser-level proof becomes ambiguous.

## Inputs

- `console/src/components/ledger/ledger-filters.tsx` — current hard-coded route-target options that omit embeddings.
- `console/src/components/ledger/ledger-filters.test.tsx` — existing focused unit coverage for the filter surface.
- `console/src/app/(console)/observability/page.tsx` — current wiring from filter state to the usage-ledger query.
- `console/src/lib/admin-api.ts` — shared admin API client that encodes `routeTarget` into `route_target`.

## Expected Output

- `console/src/components/ledger/ledger-filters.tsx` — updated route-target option list including embeddings.
- `console/src/components/ledger/ledger-filters.test.tsx` — focused regression coverage for embeddings filter selection.
- `console/src/app/(console)/observability/page.tsx` — preserved or minimally adjusted filter wiring if needed to keep the shared query path intact.
- `console/src/lib/admin-api.ts` — unchanged or minimally clarified shared filter contract if the test needs a typed reference point.
