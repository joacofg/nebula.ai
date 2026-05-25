# S04: S04 — UAT

**Milestone:** M010
**Written:** 2026-05-23T20:23:56.207Z

# UAT Type
Operational recovery proof walkthrough

# Preconditions
1. Repository is checked out at `/Users/joaquinfernandezdegamboa/Proj/nebula`.
2. Python virtualenv dependencies are installed so `.venv/bin/pytest` is available.
3. Reviewer/operator has access to the existing runtime truth surfaces referenced by the recovery proof: `/health/ready`, `/health/dependencies`, and the console runtime-health/Observability seams.

# Steps
1. Open `docs/m010-recovery-proof.md` and follow the canonical proof order from trust boundary framing to health evidence, serving-path consequence, and post-recovery confirmation.
2. Run `.venv/bin/pytest tests/test_phase10_outage_safety.py tests/test_health.py -q`.
3. Inspect the governance recovery scenario in the test output/source path referenced by the doc and confirm it covers outage -> fail-closed request behavior -> recovery -> successful serving.
4. Confirm the same governance proof asserts `/health/ready` and `/health/dependencies` return truthful post-recovery metadata, including recovery evidence fields such as `last_failure_at` and `last_recovery_at`.
5. Inspect the semantic-cache recovery scenario and confirm it covers degraded serving during outage, a `recovering` transition, and a final `ready` state on the existing health seams while chat serving remains available.
6. Use the proof document to trace which existing console/runtime-health surfaces should corroborate the same state transitions without introducing a new resilience dashboard.
7. Verify the anti-goals and failure-mode sections make it obvious what would count as recovery drift or scope creep.

# Expected Outcomes
1. The pytest command passes.
2. Governance-store recovery is proven to restore successful serving after an outage that previously forced fail-closed behavior.
3. Semantic-cache recovery is proven to move from degraded to recovering to ready while preserving serving continuity where intended.
4. Existing health surfaces provide truthful post-recovery evidence rather than stale outage claims.
5. The proof document provides a bounded, pointer-first operator review path using existing surfaces only.

# Edge Cases
- Unrelated optional dependencies may remain degraded; recovery confirmation should rely on per-dependency truth and evidence fields rather than assuming aggregate readiness is globally healthy in every scenario.
- A dependency that leaves `recovering` uncleared or fails to stamp recovery evidence should be treated as a recovery-drift signal even if some serving paths appear restored.
- Any proposed recovery workflow that depends on a new dashboard, new resilience-only API, or hosted-authoritative control plane is outside the proven scope.

# Not Proven By This UAT
- Live infrastructure restart automation or chaos-platform orchestration.
- Recovery behavior for every possible dependency class beyond the governance-store and semantic-cache paths covered here.
- A new operator console or incident-management workflow beyond the existing runtime-health and Observability seams.
