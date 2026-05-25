# S03: S03 — UAT

**Milestone:** M010
**Written:** 2026-05-23T20:12:57.949Z

# UAT Type
Operator workflow verification

# Preconditions
- Console dependencies are installed (`npm --prefix console install` already completed in the environment).
- The operator can run the focused console Vitest suites from the repository root.
- The console codebase contains the S03 runtime health and Observability updates.

# Steps
1. From the repository root, run `npm --prefix console run test -- --run src/components/health/runtime-health-cards.test.tsx`.
2. Confirm the runtime health card suite passes and covers dependency card rendering for degraded, fail-closed, recovering, and legacy-compatible payload shapes.
3. From the repository root, run `npm --prefix console run test -- --run 'src/app/(console)/observability/page.test.tsx' 'src/app/(console)/observability/observability-page.test.tsx'`.
4. Confirm the Observability suites pass and preserve the request-first page framing while showing dependency-specific resilience metadata for governance fail-closed, semantic-cache degraded serving, and premium-provider recovery examples.
5. Review the relevant assertions in the passing suites to confirm operators can see dependency identity, dependency class, serving effect, reason code, recovering state, and failure/recovery timestamps on existing surfaces without a new dashboard abstraction.

# Expected Outcomes
- Runtime health cards render resilience metadata from the additive dependency payload without breaking legacy `status` / `required` / `detail` compatibility.
- Existing Observability surfaces continue to center selected request evidence while also exposing dependency degradation and recovery truth.
- Focused Vitest verification passes with no failing assertions.

# Edge Cases
- Legacy dependency payloads that omit new resilience fields still render correctly using the old fields.
- Multiple dependencies can show repeated labels like recovery timestamps without causing ambiguous assertions or dropped operator-visible metadata.
- Recovering dependencies display recovery state independently from fully healthy dependencies.

# Not Proven By This UAT
- Full browser-executed Playwright verification of the Observability page in a compiled console build.
- Backend outage simulation or live dependency recovery beyond the stubbed/request-first console proofs already covered by the passing focused tests.
