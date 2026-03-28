---
id: S04
parent: M005
milestone: M005
provides:
  - Tenant-scoped recommendation and cache-summary contract (`RecommendationBundle`) for use by downstream proof and UI work.
  - Admin-only recommendations endpoint with deterministic bounded structure and tenant scoping.
  - Console Observability recommendation cards and cache-effectiveness/runtime context grounded in ledger-backed traffic.
  - Semantic-cache tuning controls in the existing policy preview/save flow via similarity threshold and max entry age fields.
requires:
  - slice: S02
    provides: S02’s replay/simulation posture and shared policy-editing save/preview flow, reused to keep recommendation wording and cache tuning grounded in recent ledger-backed traffic rather than ad-hoc UI heuristics.
  - slice: S03
    provides: S03’s hard-budget outcomes and runtime policy evidence vocabulary, reused as recommendation inputs and preserved as part of the operator-visible decisioning story.
affects:
  - S05
key_files:
  - src/nebula/models/governance.py
  - src/nebula/services/recommendation_service.py
  - src/nebula/api/routes/admin.py
  - migrations/versions/20260328_0008_cache_policy_controls.py
  - console/src/app/(console)/observability/page.tsx
  - console/src/components/policy/policy-form.tsx
  - console/src/lib/admin-api.ts
  - console/src/lib/query-keys.ts
  - tests/test_service_flows.py
  - tests/test_governance_api.py
  - console/src/app/(console)/observability/observability-page.test.tsx
  - console/src/components/policy/policy-page.test.tsx
key_decisions:
  - Validated recommendation feedback as a bounded, typed, tenant-scoped read model (`RecommendationBundle`) instead of endpoint-specific or free-form analytics payloads.
  - Added only two explicit semantic-cache tuning knobs to tenant policy — similarity threshold and max entry age hours — and kept the rest of cache behavior opaque to operators.
  - Kept recommendation generation strictly read-only and grounded in usage-ledger rows plus coarse semantic-cache runtime health, not raw prompts, opaque scoring, or cache-entry inspection.
  - Reused the existing RecommendationBundle DTO as the sole admin recommendations contract instead of adding a second translation layer.
  - Kept recommendation rendering inside Observability while making cache tuning inspection-only there; edits remain confined to the existing policy save/preview flow.
  - Backfilled the missing Alembic migration for the new cache policy fields so the assembled API contract matches the persisted schema.
patterns_established:
  - Bound operator guidance should ship as a typed, bounded read model backed by persisted evidence plus coarse runtime context, not as free-form analytics payloads.
  - When adding tunable runtime controls, keep inspection in Observability but keep mutation inside the existing policy preview/save contract rather than spawning a new management surface.
  - Schema-bearing TenantPolicy changes need persistence, migration, API contract, UI typing, and focused verification updated together or the assembled control-plane story breaks at startup before feature behavior is tested.
observability_surfaces:
  - `GET /v1/admin/tenants/{tenant_id}/recommendations` returns the bounded recommendation/cache summary used by the console and future proof work.
  - Observability now shows grounded recommendation cards, cache-effectiveness metrics, cache runtime status/detail, and supporting dependency-health context.
  - The policy editor now renders semantic-cache similarity threshold and max entry age as runtime-enforced controls within the existing preview/save workflow.
drill_down_paths:
  - .gsd/milestones/M005/slices/S04/tasks/T01-SUMMARY.md
  - .gsd/milestones/M005/slices/S04/tasks/T02-SUMMARY.md
  - .gsd/milestones/M005/slices/S04/tasks/T03-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-03-28T04:14:55.645Z
blocker_discovered: false
---

# S04: Recommendations and cache controls

**Delivered tenant-scoped recommendation feedback and semantic-cache tuning controls through a bounded backend read model, a narrow admin contract, and integrated Observability/policy console surfaces.**

## What Happened

S04 turned Nebula’s existing evidence and cache posture into a new operator decisioning layer without widening the product into analytics or autonomous optimization. The backend now exposes stable recommendation and cache-summary DTOs plus two explicit semantic-cache controls on tenant policy. A new `RecommendationService` derives deterministic, tenant-scoped recommendations from recent usage-ledger records, hard-budget and policy outcomes, premium-cost patterns, cache-hit behavior, and semantic-cache health, but it never mutates policy, usage, or cache data. That typed read model is exposed through a single admin-only tenant-scoped endpoint and reused directly by the console contract. On the operator side, Observability now renders bounded next-best-action cards with explicit wording that they are based on recent ledger-backed traffic plus supporting runtime context, alongside cache-effectiveness and degraded-runtime context. Cache tuning remains intentionally narrow: operators can inspect the current threshold and max-entry-age settings in Observability, but editing stays in the existing policy save/preview flow, where the policy form now validates and submits the new runtime-enforced cache controls with explicit preview-before-save semantics. During close-out verification, the assembled worktree also surfaced a missing Alembic migration for the new policy fields; adding that migration ensured the shipped TenantPolicy contract, database schema, and governance API startup behavior now align. Together, the slice delivers grounded recommendation-grade feedback and tunable semantic-cache controls while preserving Nebula’s metadata-boundary discipline and scope constraints.

## Verification

Slice-level verification passed in the assembled worktree: `./.venv/bin/pytest tests/test_service_flows.py -k "recommendation or cache" -x` (5 passed), `./.venv/bin/pytest tests/test_governance_api.py -k "recommendation or cache" -x` (6 passed), and `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx` (4 files, 14 tests passed). These cover deterministic recommendation ordering, bounded output, degraded-cache insight propagation, admin protection and tenant scoping, observability recommendation framing, and cache-control preview/save semantics.

## Requirements Advanced

- R042 — Delivered the bounded recommendation-grade feedback loop across backend service, admin contract, and observability rendering, converting recommendation guidance from a planned capability into a shipped operator surface.
- R043 — Made semantic cache behavior tunable and inspectable per tenant through explicit policy knobs, bounded cache summaries, and console save/preview semantics.
- R044 — Preserved v4 scope discipline by keeping recommendation feedback metadata-backed, read-only, tenant-scoped, and inside existing admin surfaces rather than widening into analytics, SDK, or hosted-authority work.

## Requirements Validated

- R042 — Recommendation guidance is now exposed as a deterministic tenant-scoped `RecommendationBundle` derived from recent ledger-backed traffic and coarse runtime cache health, surfaced through `GET /v1/admin/tenants/{tenant_id}/recommendations`, and rendered in Observability with explicit non-black-box wording. Verified by the focused backend, API, and Vitest runs listed below.
- R043 — Semantic cache tuning is now inspectable and editable per tenant through explicit policy fields for similarity threshold and max entry age, a bounded cache summary read model, and the existing policy save/preview flow. Verified by the same focused backend, API, and Vitest runs listed below.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

Added `migrations/versions/20260328_0008_cache_policy_controls.py` to backfill the new semantic-cache policy fields after API verification exposed a schema mismatch. No slice-plan scope widening beyond that migration hygiene fix was required.

## Known Limitations

Recommendations remain descriptive and bounded to the most recent ledger window and current cache runtime state. The slice intentionally does not add autonomous policy changes, long-horizon analytics, deep cache-entry inspection, or a dedicated cache-management surface.

## Follow-ups

S05 should assemble this new recommendation/cache surface into the full v4 proof, showing how adaptive routing, simulation, hard guardrails, and recommendations fit together without implying autonomous optimization or analytics-platform scope.

## Files Created/Modified

- `src/nebula/models/governance.py` — Added bounded recommendation/cache DTOs and explicit semantic-cache policy knobs shared across runtime, API, and UI surfaces.
- `src/nebula/services/recommendation_service.py` — Implemented deterministic, read-only tenant recommendation and cache-summary derivation from ledger-backed evidence plus coarse runtime cache health.
- `src/nebula/core/container.py` — Wired recommendation service into the application container for admin/API use.
- `src/nebula/services/governance_store.py` — Persisted the new semantic-cache tuning fields through governance storage and ORM-backed policy loading/saving.
- `src/nebula/db/models.py` — Added backing ORM columns for semantic-cache tuning controls.
- `migrations/versions/20260328_0008_cache_policy_controls.py` — Added an idempotent Alembic revision for semantic-cache tuning columns so governance/API startup matches the shipped TenantPolicy contract.
- `tests/test_service_flows.py` — Added focused backend service coverage for deterministic recommendation ordering, bounded output, degraded-cache insight behavior, and no-mutation guarantees.
- `tests/test_governance_api.py` — Added admin recommendations endpoint coverage for auth, tenant scoping, 404 behavior, bounded structure, and degraded cache evidence propagation.
- `console/src/lib/admin-api.ts` — Extended the shared console admin contract with recommendation/cache types and typed tenant policy cache-tuning fields.
- `console/src/lib/query-keys.ts` — Added a dedicated React Query key for tenant recommendations.
- `console/src/app/(console)/observability/page.tsx` — Rendered grounded recommendation cards and cache-effectiveness/runtime context in the existing Observability surface.
- `console/src/components/policy/policy-form.tsx` — Kept cache tuning in the existing policy editor with explicit preview/save semantics and validation for similarity threshold and entry age.
- `console/src/app/(console)/observability/page.test.tsx` — Locked the observability and policy UX contract with focused Vitest coverage for recommendation framing, cache insight visibility, and cache-control save/preview behavior.
- `console/src/app/(console)/observability/observability-page.test.tsx` — Locked the observability integrated wording and cache-effectiveness summary behavior with focused UI assertions.
- `console/src/components/policy/policy-form.test.tsx` — Locked cache-tuning validation and preview/save semantics in the policy editor.
- `console/src/components/policy/policy-page.test.tsx` — Locked cache-tuning grouping and operator-facing copy on the policy page.
