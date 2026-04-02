---
estimated_steps: 6
estimated_files: 5
skills_used: []
---

# T03: Render bounded calibration evidence in Observability and request detail

Expose the new summary to operators through existing console surfaces without turning them into analytics dashboards.

Steps:
1. Update `console/src/components/ledger/ledger-request-detail.tsx` to render a compact calibration-evidence block that explains sufficient, stale, thin, or rollout-disabled state in request-adjacent operator language while preserving the per-request ledger story as primary.
2. Update `console/src/app/(console)/observability/page.tsx` to show tenant-scoped calibration evidence as bounded supporting context alongside persisted ledger evidence and recommendations, not as a separate analytics destination.
3. Add focused Vitest coverage in `console/src/components/ledger/ledger-request-detail.test.tsx` and `console/src/app/(console)/observability/observability-page.test.tsx` for sufficient/stale/thin/disabled messaging, graceful handling when summaries are absent, and the guardrail that Observability remains the persisted explanation surface rather than a replacement for ledger proof.
4. Keep copy derived from runtime/admin truth: calibration evidence should explain ledger-backed state, gated rollout, and replay readiness without inventing new runtime entities or promising raw-outcome analytics.

## Inputs

- `console/src/lib/admin-api.ts`
- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`
- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `src/nebula/api/routes/admin.py`
- `src/nebula/models/governance.py`

## Expected Output

- `console/src/lib/admin-api.ts`
- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`
- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`

## Verification

npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/app/'(console)'/observability/observability-page.test.tsx
