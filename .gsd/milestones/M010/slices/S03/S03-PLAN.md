# S03: Operator-visible resilience state

**Goal:** Make existing console observability surfaces show dependency-specific resilience state and recovery metadata so operators can identify failed dependencies, degraded mode, and recovery status without leaving the current request-first workflow or introducing a new dashboard.
**Demo:** After this: operators can use existing health/admin/request-detail/Observability surfaces to identify the failed dependency, understand the current degraded mode, and see recovery status without a new dashboard.

## Must-Haves

- Observability consumes the additive runtime health contract already emitted by `/health/dependencies` and preserves those fields through the console typing seam.
- Runtime dependency cards visibly show dependency class, serving effect, reason code, and recovery timestamps/flags for serving-critical, serving-optional, and recovering examples while remaining compatible with legacy `status`/`required`/`detail` payloads.
- Existing request-first observability tests and browser proof demonstrate operators can inspect governance fail-closed, semantic-cache degraded-serving, and recovering state examples on existing surfaces without reframing the page as a separate resilience dashboard.

## Proof Level

- This slice proves: integration

## Integration Closure

This slice closes the operator-visible leg of the resilience milestone by wiring the backend’s additive dependency contract into existing console health and observability surfaces. No new API or dashboard is introduced; remaining milestone work is only the end-to-end recovery/runbook proof in S04 and the integrated pointer-first proof in S05.

## Verification

- Operators gain concrete UI visibility into `dependency_class`, `lifecycle_state`, `serving_effect`, `reason_code`, `recovering`, `last_failure_at`, and `last_recovery_at` on the existing Observability dependency-health section, with tests proving the local runtime truth survives the console proxy untouched.

## Tasks

- [x] **T01: Wire resilience metadata into runtime health cards** `est:75m`
  Why: S01/S02 already emit a richer additive dependency contract, but the console currently narrows it away and the health cards silently drop most operator-relevant resilience fields, which blocks R088 on the main operator surface.
  - Files: `console/src/lib/admin-api.ts`, `console/src/components/health/runtime-health-cards.tsx`, `console/src/components/health/runtime-health-cards.test.tsx`
  - Verify: npm --prefix console run test -- --run src/components/health/runtime-health-cards.test.tsx

- [x] **T02: Prove request-first observability surfaces expose outage and recovery truth** `est:90m`
  Why: S03 is only complete if operators can actually inspect dependency-specific outage and recovery state on existing Observability surfaces without displacing the selected request evidence hierarchy established in M009.
  - Files: `console/src/app/(console)/observability/page.tsx`, `console/src/app/(console)/observability/page.test.tsx`, `console/src/app/(console)/observability/observability-page.test.tsx`, `console/e2e/observability.spec.ts`, `console/src/app/api/runtime/health/route.ts`
  - Verify: npm --prefix console run test -- --run src/app/(console)/observability/page.test.tsx src/app/(console)/observability/observability-page.test.tsx

## Files Likely Touched

- console/src/lib/admin-api.ts
- console/src/components/health/runtime-health-cards.tsx
- console/src/components/health/runtime-health-cards.test.tsx
- console/src/app/(console)/observability/page.tsx
- console/src/app/(console)/observability/page.test.tsx
- console/src/app/(console)/observability/observability-page.test.tsx
- console/e2e/observability.spec.ts
- console/src/app/api/runtime/health/route.ts
