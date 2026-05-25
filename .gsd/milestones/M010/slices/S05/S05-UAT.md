# S05: S05 — UAT

**Milestone:** M010
**Written:** 2026-05-23T20:38:31.135Z

# UAT: M010 integrated resilience proof discoverability and review path

## UAT Type
Documentation and review-path verification

## Preconditions
1. Repository worktree is available with the M010 documentation updates.
2. Reviewer can open `README.md`, `docs/architecture.md`, `docs/m010-recovery-proof.md`, and `docs/m010-integrated-proof.md`.
3. Reviewer understands that runtime health endpoints and existing console surfaces are the intended evidence seams for M010.

## Steps
1. Open `README.md` and navigate to the documentation map.
2. Confirm there is an entry for `docs/m010-integrated-proof.md` describing it as the integrated resilience proof.
3. Open `docs/architecture.md` and confirm it links to `docs/m010-integrated-proof.md` as the resilience close-out review path.
4. Open `docs/m010-recovery-proof.md` and confirm it links upward to `docs/m010-integrated-proof.md` as the higher-level close-out sequence.
5. Open `docs/m010-integrated-proof.md` and read the canonical proof order.
6. Confirm the review order starts from the hosted-boundary/local-authority framing, then points reviewers to `/health/ready` and `/health/dependencies` as first authority.
7. Confirm the document distinguishes governance-store fail-closed behavior from semantic-cache degraded continuity and points to `tests/test_phase10_outage_safety.py` and `tests/test_health.py` for executable anti-drift proof.
8. Confirm the document names Observability and runtime health cards as supporting operator corroboration surfaces, not replacement authority.
9. Confirm the document routes recovery confirmation through `docs/m010-recovery-proof.md` and the same shipped runtime health surfaces.
10. Confirm the anti-sprawl boundaries explicitly reject a new resilience dashboard, a new resilience API family, hosted-authoritative recovery claims, and a broader chaos platform story.

## Expected Outcomes
- Reviewers can discover the integrated proof from repo entry documentation without prior milestone context.
- The integrated proof provides one coherent pointer-first walkthrough joining outage trigger, degraded runtime truth, operator corroboration, and recovery confirmation.
- `/health/ready` and `/health/dependencies` are clearly treated as authoritative runtime truth.
- Console surfaces are clearly presented as corroboration only.
- The proof remains bounded to existing runtime, console, and test seams already validated earlier in M010.

## Edge Cases
- If the integrated proof exists but is not linked from entry docs, the milestone close-out path is still too siloed.
- If the integrated proof starts restating full endpoint or UI contracts instead of pointing to canonical sources, anti-duplication boundaries have drifted.
- If the proof implies hosted status or console views are authoritative for serving-time recovery truth, the trust boundary has regressed.
- If governance fail-closed and semantic-cache degraded continuity are not kept distinct, the resilience story has collapsed important outage classes.

## Not Proven By This UAT
- Live execution of outage or recovery scenarios.
- Runtime correctness of `/health/ready`, `/health/dependencies`, Observability, or runtime health cards beyond the already-validated upstream slices.
- New telemetry, operator workflows, or broader incident-management capabilities outside the bounded M010 scope.
