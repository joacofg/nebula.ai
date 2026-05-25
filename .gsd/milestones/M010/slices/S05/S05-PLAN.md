# S05: Integrated resilience proof

**Goal:** Assemble the final M010 integrated resilience proof into one pointer-first review path and wire discoverability links so reviewers can find the outage, operator-inspection, and recovery evidence without widening product scope.
**Demo:** After this: one integrated proof shows outage trigger, degraded runtime truth, operator inspection, and successful recovery confirmation in a pointer-first review path with anti-sprawl boundaries locked.

## Must-Haves

- `docs/m010-integrated-proof.md` exists and provides a pointer-first review order that joins local trust boundary, health-surface outage truth, governance fail-closed behavior, semantic-cache degraded-serving behavior, operator corroboration on existing console surfaces, and recovery confirmation.
- The integrated proof explicitly keeps `/health/ready` and `/health/dependencies` authoritative, treats console surfaces as corroboration only, and preserves anti-sprawl boundaries: no new resilience dashboard, no new resilience API family, no hosted-authoritative recovery story, and no implied chaos platform.
- Repo entry docs link to the new integrated proof so M010 is discoverable alongside prior milestone proofs.
- Verification proves the integrated doc and discoverability links exist on disk and that the proof references the bounded M010 seams already validated in S02-S04.

## Proof Level

- This slice proves: final-assembly

## Integration Closure

This slice consumes the already-validated outage/runtime seams from `tests/test_phase10_outage_safety.py` and `tests/test_health.py`, the operator corroboration seams in `console/src/app/(console)/observability/page.tsx` and `console/src/components/health/runtime-health-cards.tsx`, and the bounded recovery walkthrough in `docs/m010-recovery-proof.md`. It introduces no new runtime wiring; closure is achieved when one integrated document plus discoverability links let a reviewer traverse the complete proof without reopening backend or console implementation work.

## Verification

- No new runtime telemetry is added. The slice improves proof discoverability for the existing observability surfaces by documenting `/health/ready`, `/health/dependencies`, runtime health cards, and the Observability page as the canonical outage and recovery inspection path while preserving local-runtime authority over hosted or console corroboration.

## Tasks

- [x] **T01: Author the integrated M010 resilience proof document** `est:45m`
  Why: M010 already has validated outage, operator-surface, and recovery seams, but the milestone still needs one canonical close-out path that tells reviewers where to look and in what order without duplicating contracts or widening scope.
  - Files: `docs/m010-integrated-proof.md`
  - Verify: python3 -c "from pathlib import Path; p = Path('docs/m010-integrated-proof.md'); assert p.exists() and p.stat().st_size > 0; print(p.stat().st_size)"

- [x] **T02: Wire M010 proof discoverability from entry docs** `est:20m`
  Why: The integrated proof only closes the milestone if reviewers can find it from the repository’s main documentation index and architecture proof chain. Without discoverability, the proof remains siloed and easy to miss.
  - Files: `README.md`, `docs/architecture.md`, `docs/m010-recovery-proof.md`, `docs/m010-integrated-proof.md`
  - Verify: rg -n "m010-integrated-proof" README.md docs/architecture.md docs/m010-recovery-proof.md docs/m010-integrated-proof.md

## Files Likely Touched

- docs/m010-integrated-proof.md
- README.md
- docs/architecture.md
- docs/m010-recovery-proof.md
