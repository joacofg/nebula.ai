# S04: Recovery verification and runbook proof

**Goal:** Verify and document end-to-end recovery paths for the highest-value outage classes using existing runtime and operator truth surfaces, proving restored healthy behavior plus trustworthy post-recovery evidence without adding new resilience APIs or dashboards.
**Demo:** After this: a documented recovery path for the highest-value outage classes is verified end to end, including restored healthy behavior and trustworthy post-recovery evidence.

## Must-Haves

- Deterministic backend recovery tests prove governance-store fail-closed outage can recover to successful serving with `/health/ready` and `/health/dependencies` returning truthful post-recovery state.
- Deterministic backend recovery tests prove semantic-cache degraded serving can transition through recovering/ready semantics and clear back to trustworthy healthy evidence.
- A pointer-first recovery proof document under `docs/` gives operators one bounded review path across existing health and Observability seams, explicitly reusing existing canonical sources and avoiding dashboard/control-plane scope creep.
- Slice verification passes with focused pytest coverage for outage/recovery transitions and at least one mechanical check that the recovery proof document exists and is non-empty.

## Proof Level

- This slice proves: integration + operational proof on deterministic runtime seams; no new runtime surface required, no browser UAT required unless a later slice needs it.

## Integration Closure

Consumes the typed resilience contract and outage/operator evidence from S02 and S03, extends the existing outage harness with recovery transitions, and closes the milestone recovery gap by binding request behavior, health payload truth, and operator-facing recovery walkthrough into one bounded proof path. After this slice, S05 can assemble the final integrated resilience proof without inventing new recovery semantics.

## Verification

- Strengthens existing `/health/ready`, `/health/dependencies`, and console Observability seams by proving that recovery transitions truthfully supersede outage state and remain inspectable through existing dependency metadata fields (`recovering`, `last_failure_at`, `last_recovery_at`).

## Tasks

- [x] **T01: Add deterministic recovery transition proofs for governance and semantic-cache outages** `est:4-6h`
  Why: S02 proved outage truth, but S04 owns the missing recovery leg: the same high-value dependency classes must recover cleanly without stale fail-closed or degraded claims lingering on existing health surfaces. Do: extend `tests/test_phase10_outage_safety.py` with stateful doubles or harness updates that exercise governance-store outage → recovery to successful serving and semantic-cache degraded outage → recovering/ready truth; add or tighten focused health-contract coverage in `tests/test_health.py` only if needed to lock the aggregate `recovering` semantics. Reuse existing deterministic support seams from `tests/support.py` and the additive payload builder from `src/nebula/models/resilience.py`; do not add network-chaos infrastructure or new endpoints. Done when: focused pytest coverage proves request behavior, `/health/ready`, and `/health/dependencies` all move truthfully across outage and recovery states for governance and semantic-cache paths, including explicit post-recovery evidence fields where applicable.
  - Files: `tests/test_phase10_outage_safety.py`, `tests/test_health.py`, `tests/support.py`
  - Verify: .venv/bin/pytest tests/test_phase10_outage_safety.py tests/test_health.py -q

- [x] **T02: Write the bounded M010 recovery proof walkthrough** `est:2-3h`
  Why: S04 must leave behind an operator-usable, pointer-first recovery proof path that tells reviewers exactly how to inspect outage evidence, perform recovery confirmation, and verify post-recovery truth without widening the product. Do: create `docs/m010-recovery-proof.md` modeled on the pointer-first structure of `docs/m009-integrated-proof.md`, anchored to existing `/health/ready`, `/health/dependencies`, and console Observability/runtime-health seams plus the new deterministic recovery tests from T01. Include canonical sources, minimal proof order, what counts as recovery confirmation, anti-goals around new dashboards and hosted authority, and a concise failure-mode section that makes drift obvious. Keep hosted/control-plane wording subordinate to `docs/hosted-reinforcement-boundary.md`. Done when: the doc is non-empty, references the current recovery-proof seams, and can guide a reviewer from outage truth through recovered behavior and operator-visible evidence using only existing surfaces.
  - Files: `docs/m010-recovery-proof.md`
  - Verify: python3 -c "from pathlib import Path; p = Path('docs/m010-recovery-proof.md'); assert p.exists() and p.stat().st_size > 0"

## Files Likely Touched

- tests/test_phase10_outage_safety.py
- tests/test_health.py
- tests/support.py
- docs/m010-recovery-proof.md
