# Research — S03: Operator-visible resilience state

## Summary
S03 is targeted research, not deep discovery. The backend resilience contract already exists and is exercised in S01/S02 on `/health/ready` and `/health/dependencies`; the missing work is mainly console/operator-surface adoption of the richer payload and bounded verification that operators can identify failed dependency, degraded mode, and recovery state without creating a new dashboard. This slice supports R088 directly and builds on S01/S02 proofs for R086/R087.

## Active requirements and slice constraints
- **R088** is the center of gravity: existing health/admin/request-detail/Observability surfaces must show dependency-specific failure state, last meaningful failure context, and recovery status.
- Keep the **request-first hierarchy** from M009: selected request evidence remains authoritative, with health/observability as supporting context only. This is reinforced by MEM051 and the current Observability copy.
- Keep the **existing-surface rule** from milestone context and MEM047: strengthen current cards/pages, do not introduce a new resilience dashboard or separate incident workflow.
- Hosted/control-plane posture can remain supporting only; S03 should not make hosted freshness/dependency summaries authoritative over local runtime truth.

## Recommendation
Treat S03 as two natural seams, with backend only if a thin adapter is needed:
1. **Runtime-health payload consumption + presentation** in the console so operators can see typed resilience fields already emitted by the backend (`dependency_class`, `lifecycle_state`, `serving_effect`, `reason_code`, `recovering`, `last_failure_at`, `last_recovery_at`).
2. **Verification updates** across unit/page/e2e tests to prove both serving-critical and serving-optional examples are inspectable on existing Observability/runtime health surfaces, and that recovery metadata is visible when present.

First proof should be the UI contract test around `RuntimeHealthCards`, because that is the narrowest seam where S03 can fail: today the UI only renders `status/detail` plus retention-specific metrics, so most resilience fields from S01 are silently dropped.

## Implementation landscape
### Backend/runtime truth already present
- `src/nebula/models/resilience.py`
  - Canonical additive payload builder. Typed keys already standardized: `dependency_class`, `lifecycle_state`, `serving_effect`, `reason_code`, `recovering`, `last_failure_at`, `last_recovery_at`.
- `src/nebula/services/runtime_health_service.py`
  - `readiness()` returns `{status, runtime_profile, dependencies}`.
  - `dependencies()` already aggregates gateway, governance_store, semantic_cache, local_ollama, premium_provider, retention_lifecycle.
- `src/nebula/main.py`
  - `/health/ready` returns readiness JSON with 200 for `ready|degraded`, 503 for `not_ready`.
  - `/health/dependencies` currently returns the same `runtime_health_service.readiness()` payload, not a narrower dependencies-only structure.
- S02 tests prove concrete outage payloads already exist for `governance_store` and `semantic_cache` in `tests/test_phase10_outage_safety.py` and `tests/test_health.py`.

### Console/operator surfaces already present
- `console/src/app/api/runtime/health/route.ts`
  - Server proxy that auth-checks admin session, then fetches `/health/dependencies` from the gateway.
  - No transformation layer today; whatever backend returns is passed through.
- `console/src/app/(console)/observability/page.tsx`
  - Already frames Observability as **selected request evidence first** and renders dependency health as subordinate runtime context.
  - `runtimeHealthQuery` currently types dependencies as only `{status, required, detail}`, so typed resilience fields are not modeled in TS even though they can flow through.
- `console/src/components/health/runtime-health-cards.tsx`
  - Generic card renderer, but currently only surfaces `status`, `detail`, and retention-specific extra metrics (`last_status`, `last_run_at`, etc.).
  - This is the primary seam for S03.
- `console/src/components/ledger/ledger-request-detail.tsx`
  - Strong request-first evidence surface already exists. Likely no major resilience data change needed here unless planner wants a small explanatory copy tweak.

### Existing tests that should be extended, not bypassed
- `console/src/components/health/runtime-health-cards.test.tsx`
  - Best first proof target. Add assertions for resilience fields and recovery timestamps.
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
  - Both already assert bounded, non-dashboard framing. Extend mocks/assertions to prove failed dependency name, degraded mode, reason/recovery context appear while request-first ordering remains intact.
- `console/e2e/observability.spec.ts`
  - Existing e2e already stubs `/api/runtime/health`; evolve it with typed dependency payloads and visible operator checks instead of inventing new routes.

## Gaps / what is missing now
1. **Typed resilience metadata is produced but not meaningfully shown in the UI.**
   - `RuntimeHealthCards` ignores `dependency_class`, `serving_effect`, `reason_code`, `recovering`, `last_failure_at`, `last_recovery_at`, and even `enabled`.
2. **TypeScript contract is stale/minimal.**
   - `console/src/lib/admin-api.ts` defines `RuntimeHealthDependency` without resilience fields, so the intended operator contract is not explicit on the console side.
   - `ObservabilityPage` locally narrows the fetch type even further.
3. **Recovery visibility is only covered in backend tests today.**
   - `tests/test_health.py` proves recovering payloads exist, but no console test proves operators can see them.
4. **Hosted deployment dependency pills use a different coarse contract.**
   - `console/src/components/deployments/dependency-health-pills.tsx` consumes heartbeat `dependency_summary` (`healthy/degraded/unavailable` arrays). This is useful context but should stay separate from S03’s local-runtime truth; avoid trying to unify them in this slice.

## Likely file targets and purpose
- `console/src/lib/admin-api.ts`
  - Expand `RuntimeHealthDependency` to include additive resilience fields and timestamp fields used by operator UI.
- `console/src/app/(console)/observability/page.tsx`
  - Update fetch typing/copy only as needed; keep request-first framing and use `RuntimeHealthCards` as the presentation seam.
- `console/src/components/health/runtime-health-cards.tsx`
  - Main implementation target. Render resilience metadata in a bounded way, likely as labeled rows/chips: class, serving effect, reason code, recovering, last failure, last recovery, plus existing retention metrics.
- `console/src/components/health/runtime-health-cards.test.tsx`
  - Unit proof for governance fail-closed, semantic-cache degraded, and recovering states.
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
  - Page-level proof that operator-visible resilience state appears while request-first hierarchy remains intact.
- `console/e2e/observability.spec.ts`
  - Browser proof using stubbed runtime health payloads.
- Optional only if needed: `console/src/app/api/runtime/health/route.ts`
  - Likely unchanged; only touch if planner wants explicit response typing or passthrough tests.

## Natural seams for planner decomposition
### Seam A — Shared console contract + card rendering
Independent work unit:
- Add typed resilience fields to `RuntimeHealthDependency`.
- Teach `RuntimeHealthCards` to render additive resilience rows without changing page architecture.
- Keep retention lifecycle special metrics intact.

### Seam B — Observability page verification
Independent after or parallel with Seam A if scoped to tests/copy:
- Extend page and e2e tests with realistic governance/semantic-cache/recovering payloads.
- Verify dependency-specific identification, degraded mode explanation, and recovery timestamps/status are visible.
- Reassert no dashboard-sprawl wording regression.

### Seam C — Thin backend/proxy touch (only if tests reveal mismatch)
Potentially zero-code:
- Confirm `/api/runtime/health` and `/health/dependencies` passthrough preserve all typed fields.
- Only modify if an intermediate serializer or typing assumption drops keys; current code suggests passthrough is already adequate.

## First proof / highest-risk check
Start with `console/src/components/health/runtime-health-cards.test.tsx` and make it express the slice acceptance in miniature:
- a `governance_store` dependency with `dependency_class: serving_critical`, `serving_effect: fail_closed`, `reason_code: governance_query_failed`, `recovering: false`
- a `semantic_cache` dependency with `dependency_class: serving_optional`, `serving_effect: continuity_limited`, `reason_code: semantic_cache_unavailable`
- a recovering dependency with `lifecycle_state/status: recovering`, `recovering: true`, `last_failure_at`, `last_recovery_at`

If that contract can be rendered cleanly without UI sprawl, the rest is wiring and verification.

## Verification
Backend confidence already exists from prior slices; S03 should focus on console verification plus one backend regression check if touched.

Recommended commands:
- `npm --prefix console run test -- --run src/components/health/runtime-health-cards.test.tsx src/app/(console)/observability/page.test.tsx src/app/(console)/observability/observability-page.test.tsx`
- `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx` only if request-detail copy/ordering changes
- `npm --prefix console run e2e -- observability.spec.ts` or project-equivalent filtered Playwright invocation if configured
- Optional regression if any backend route/proxy code changes: `.venv/bin/pytest tests/test_health.py -q`

## Skill notes
Installed skills directly relevant here:
- `react-best-practices` — relevant for keeping React/Next query/render changes additive and bounded.
- `write-docs` — relevant only if copy changes become substantial, but likely unnecessary.
- `observability` — useful guidance source conceptually: preserve operator-first signals on existing surfaces instead of widening UI scope.

Promising non-installed skills discovered (do not install automatically):
- Query: `FastAPI` → `npx skills add wshobson/agents@fastapi-templates` (17.8K installs)
- Query: `Next.js` → `npx skills add vercel-labs/vercel-plugin@nextjs` (4K installs)
- Query: `React Query` → `npx skills add mindrally/skills@react-query` (688 installs)
- Query: `Playwright` → `npx skills add currents-dev/playwright-best-practices-skill@playwright-best-practices` (42.2K installs)

## Watch-outs / planner cautions
- Do not convert Observability into a resilience dashboard; preserve the existing request-first narrative and bounded supporting cards.
- Do not make hosted `dependency_summary` or freshness authoritative for local outage truth in this slice.
- Preserve additive compatibility: UI should tolerate legacy deps that only have `status/required/detail` while surfacing richer metadata when present.
- Be careful with wording around recovery: show `last_failure_at` / `last_recovery_at` as supporting evidence, not as a claim that all downstream state is healed. That milestone proof is S04.
