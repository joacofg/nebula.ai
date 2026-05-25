# S06: S06

**Goal:** Close the R087 validation gap by adding explicit outage-path proof for premium-provider and hosted metadata service classes on existing runtime truth surfaces, reusing the established resilience contract and outage harnesses without widening scope.
**Demo:** After this: M010 explicitly proves premium-provider and hosted-metadata outage behavior on existing runtime truth surfaces, closing the remaining R087 validation gap without adding new product surface area.

## Must-Haves

- Focused outage tests prove premium-provider unavailability degrades truthfully without blocking unrelated healthy local serving, with matching readiness and dependency payload evidence on existing health surfaces.
- Focused outage tests prove hosted metadata-service outage preserves serving continuity and truthful non-authoritative health/admin behavior on existing surfaces.
- The slice reuses the existing outage safety suite and resilience contract without adding new APIs, dashboards, or hosted-authoritative behavior.

## Proof Level

- This slice proves: integration

## Integration Closure

Consumes the existing typed resilience contract from S01, outage harnesses and request/health proof pattern from S02, operator-truth boundaries from S03, recovery/integrated-proof framing from S04-S05. This slice closes only the remaining requirement-evidence gap for R087; it does not introduce new runtime abstractions, UI surfaces, or recovery programs.

## Verification

- Adds deterministic verification evidence for premium-provider and hosted metadata outage classes on the existing /health/ready and /health/dependencies truth surfaces so milestone validation can cite complete outage-class coverage.

## Tasks

- [x] **T01: Add premium-provider and hosted-metadata outage proofs** `est:1.5h`
  Why: R087 explicitly names premium-provider and hosted metadata service outage classes, but M010 currently proves only governance and semantic-cache classes directly. Do: extend `tests/test_phase10_outage_safety.py` using the existing outage harnesses to add a premium-provider outage scenario that preserves healthy local serving while `/health/ready` remains non-503 and `/health/dependencies` reports `premium_provider` as serving-optional degraded continuity-limited with stable reason/detail. Also tighten or extend the existing hosted outage proof so it explicitly establishes metadata-only continuity semantics and non-authoritative truth on existing surfaces. Reuse current resilience payload helpers and keep the change test-first and bounded. Done when both outage classes are directly covered by deterministic tests and the focused outage safety suite passes.
  - Files: `tests/test_phase10_outage_safety.py`, `tests/test_health.py`, `tests/support.py`, `src/nebula/services/premium_provider_health_service.py`, `src/nebula/services/runtime_health_service.py`
  - Verify: .venv/bin/pytest tests/test_phase10_outage_safety.py tests/test_health.py -q

- [x] **T02: Update resilience proof references for full R087 coverage** `est:0.75h`
  Why: Milestone validation and integrated proof artifacts need to point at the new outage evidence so R087 can be validated honestly. Do: update the narrow M010 proof artifact(s) and slice summary inputs as needed so premium-provider and hosted-metadata outage coverage is discoverable from the canonical resilience review path, without duplicating low-level contracts. Keep changes pointer-first and bounded to existing docs. Done when the integrated proof and/or validation-facing evidence path mentions the newly added outage-class proofs clearly enough for milestone revalidation.
  - Files: `docs/m010-integrated-proof.md`
  - Verify: rg -n "premium-provider|hosted metadata|metadata-only|m010-integrated-proof" docs/m010-integrated-proof.md tests/test_phase10_outage_safety.py

## Files Likely Touched

- tests/test_phase10_outage_safety.py
- tests/test_health.py
- tests/support.py
- src/nebula/services/premium_provider_health_service.py
- src/nebula/services/runtime_health_service.py
- docs/m010-integrated-proof.md
