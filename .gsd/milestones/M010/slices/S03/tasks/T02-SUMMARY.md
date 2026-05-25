---
id: T02
parent: S03
milestone: M010
key_files:
  - console/src/app/(console)/observability/page.tsx
  - console/src/app/(console)/observability/page.test.tsx
  - console/src/app/(console)/observability/observability-page.test.tsx
  - console/e2e/observability.spec.ts
  - console/src/components/health/runtime-health-cards.tsx
key_decisions:
  - Kept `console/src/app/(console)/observability/page.tsx` aligned to the shared `RuntimeHealthDependency` contract instead of re-declaring a narrower inline dependency type.
  - Validated request-first observability proof through existing page/unit specs and refreshed the Playwright stub payloads to cover governance fail-closed, semantic-cache degraded-serving, and premium-provider recovery metadata without adding a new dashboard surface.
duration: 
verification_result: mixed
completed_at: 2026-05-23T20:11:57.367Z
blocker_discovered: false
---

# T02: Updated observability page typing and request-first specs so existing console surfaces prove dependency-specific outage and recovery metadata for governance, semantic cache, and recovery states.

**Updated observability page typing and request-first specs so existing console surfaces prove dependency-specific outage and recovery metadata for governance, semantic cache, and recovery states.**

## What Happened

Updated the Observability page runtime-health query typing to consume the shared richer dependency contract so resilience metadata is not narrowed away before rendering. Extended both observability page spec files to prove the request-first framing still leads the operator workflow while the existing dependency-health section shows dependency identity plus typed outage/recovery context for governance fail-closed, semantic-cache degraded-serving, and premium-provider recovery scenarios. Refreshed the browser proof in `console/e2e/observability.spec.ts` to stub the same richer runtime-health payloads and assert the existing page, not a new dashboard, exposes failed dependency identity, degraded serving semantics, and recovery evidence. While iterating, cleaned duplicate-tail artifacts and adjusted duplicate-label assertions to match the repeated metadata rows rendered by the shared runtime health cards.

## Verification

Passed the task-required focused Vitest verification for the existing Observability page surfaces with richer runtime-health payloads: `./node_modules/.bin/vitest --run src/app/\(console\)/observability/page.test.tsx src/app/\(console\)/observability/observability-page.test.tsx` from `console/` completed successfully with 5/5 tests passing. Attempted the refreshed Playwright browser proof via `npm run e2e -- observability.spec.ts`, but execution was blocked before the spec ran by an unrelated existing console build failure in `console/src/components/policy/policy-form.tsx`, so browser verification remains pending on that separate issue.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `cd /Users/joaquinfernandezdegamboa/Proj/nebula/console && ./node_modules/.bin/vitest --run src/app/\(console\)/observability/page.test.tsx src/app/\(console\)/observability/observability-page.test.tsx` | 0 | ✅ pass | 962ms |
| 2 | `cd /Users/joaquinfernandezdegamboa/Proj/nebula/console && npm run e2e -- observability.spec.ts` | 1 | ❌ fail (blocked by unrelated existing build/type error in console/src/components/policy/policy-form.tsx before Playwright could run) | 4753ms |

## Deviations

Updated a few duplicate-label Testing Library assertions and cleaned stray tail fragments left in touched test/component files while iterating so the focused observability specs and page typing compiled cleanly. The browser proof file was refreshed as planned, but end-to-end execution could not complete because the existing console build is blocked by an unrelated `TenantPolicy` typing mismatch in `console/src/components/policy/policy-form.tsx`.

## Known Issues

`npm --prefix console run e2e -- observability.spec.ts` is still blocked before test execution because the console build fails on an unrelated pre-existing type error in `console/src/components/policy/policy-form.tsx` (`TenantPolicy` is missing `evidence_retention_window` / related fields). The refreshed observability Playwright spec is in place, but browser proof could not be executed until that separate build issue is fixed.

## Files Created/Modified

- `console/src/app/(console)/observability/page.tsx`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/e2e/observability.spec.ts`
- `console/src/components/health/runtime-health-cards.tsx`
