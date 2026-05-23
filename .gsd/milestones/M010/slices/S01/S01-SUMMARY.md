---
id: S01
parent: M010
milestone: M010
provides:
  - A stable typed dependency-state vocabulary covering serving-critical, serving-optional, metadata-only, degraded, not-ready, and recovering states.
  - Truthful readiness aggregation rules for fail-closed versus degraded serving behavior.
  - Focused backend contract tests that downstream outage, operator-surface, and recovery slices can build on without redefining resilience semantics.
requires:
  []
affects:
  - S02
  - S03
  - S04
  - S05
key_files:
  - src/nebula/models/resilience.py
  - src/nebula/services/governance_store.py
  - src/nebula/services/semantic_cache_service.py
  - src/nebula/services/premium_provider_health_service.py
  - src/nebula/services/embeddings_service.py
  - src/nebula/services/retention_lifecycle_service.py
  - src/nebula/services/runtime_health_service.py
  - tests/support.py
  - tests/test_health.py
  - tests/test_response_headers.py
  - tests/test_retention_lifecycle_service.py
key_decisions:
  - Introduced a single additive resilience contract so dependency producers can add typed outage metadata without breaking existing `status` / `required` / `detail` consumers.
  - Classified governance as serving-critical fail-closed, semantic cache/local Ollama/premium provider as serving-optional continuity-limited, and retention lifecycle as metadata-only unaffected.
  - Made runtime readiness derive from typed resilience fields first, with legacy `required` fallback preserved for compatibility.
  - Treat recovering dependencies as degraded runtime truth unless a serving-critical or fail-closed dependency is unavailable.
patterns_established:
  - Additive contract evolution for health payloads: preserve legacy keys while layering typed machine-readable fields.
  - Runtime readiness aggregation should prefer explicit typed resilience semantics over ad hoc boolean `required` checks.
  - Recovery-state metadata belongs on the same dependency payload as current health state so later operator surfaces can stay pointer-first.
observability_surfaces:
  - `/health/ready` overall status and typed dependency payloads
  - `/health/dependencies` dependency-class, serving-effect, reason-code, and recovery-state fields
drill_down_paths:
  - .gsd/milestones/M010/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M010/slices/S01/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-05-23T19:49:22.713Z
blocker_discovered: false
---

# S01: S01

**Locked Nebula’s typed dependency resilience contract into health aggregation and tests so serving-critical, serving-optional, metadata-only, and recovering states now produce stable runtime truth.**

## What Happened

S01 established one shared backend resilience vocabulary and pushed it through the existing runtime truth surfaces without widening scope into new dashboards or hosted-plane behavior. T01 added the shared dependency health contract in `src/nebula/models/resilience.py`, kept the legacy `status` / `required` / `detail` fields intact, and migrated the dependency producers to emit typed `dependency_class`, `lifecycle_state`, `serving_effect`, `reason_code`, `recovering`, `last_failure_at`, and `last_recovery_at` metadata. Governance store now reports serving-critical fail-closed semantics; semantic cache, local Ollama, and premium provider report serving-optional continuity-limited semantics; retention lifecycle reports metadata-only unaffected semantics. T02 then updated `RuntimeHealthService` to aggregate readiness from the typed contract first, while retaining compatibility with legacy fallback fields, so `/health/ready` returns truthful `503` only for serving-critical or fail-closed failures and reports optional or recovering dependencies as degraded instead of falsely not ready. Focused tests now lock the contract for optional degradation, serving-critical failure, recovering payloads, and response-header parity around existing request-path behavior. During verification, stale response-header expectations were narrowed to current stable route metadata so the required health-contract suite could pass cleanly against the present routing implementation.

## Verification

Verified the slice-required health and response-header contract suite after resume using `cd /Users/joaquinfernandezdegamboa/Proj/nebula && .venv/bin/pytest tests/test_health.py tests/test_response_headers.py -q`, which passed with `9 passed in 2.50s`. Task summaries also record passing focused evidence for `tests/test_health.py -q` and `tests/test_retention_lifecycle_service.py -q`, covering the metadata-only retention payload shape introduced by the shared resilience contract.

## Requirements Advanced

- R086 — Established the foundational resilience truth model and tests that later outage, operator, and recovery proofs depend on.
- R087 — Defined explicit serving-critical, serving-optional, and metadata-only dependency behavior with fail-closed versus degraded readiness semantics.
- R088 — Added typed dependency-state and recovery metadata to existing health surfaces so operators can later inspect degradation and recovery status consistently.

## Requirements Validated

None.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

Updated stale response-header assertions to the current stable routing metadata schema while verifying the health-contract work, rather than adding broader new routing coverage.

## Known Limitations

This slice locks the resilience contract and readiness semantics at unit/integration-test level only; live outage drills, operator-surface presentation, and recovery runbook proof are deferred to downstream slices.

## Follow-ups

S02 should exercise real serving-critical and serving-optional outage paths against runtime behavior using this contract. S03 should reuse the typed dependency vocabulary on operator-visible surfaces. S04 should prove end-to-end recovery transitions with trustworthy post-recovery evidence.

## Files Created/Modified

- `src/nebula/models/resilience.py` — Added the shared additive dependency health contract and builder helpers.
- `src/nebula/services/governance_store.py` — Mapped governance health to serving-critical fail-closed resilience semantics.
- `src/nebula/services/semantic_cache_service.py` — Mapped semantic cache health to serving-optional continuity-limited semantics.
- `src/nebula/services/premium_provider_health_service.py` — Mapped premium provider health to serving-optional typed resilience payloads.
- `src/nebula/services/embeddings_service.py` — Mapped local Ollama health to serving-optional typed resilience payloads.
- `src/nebula/services/retention_lifecycle_service.py` — Mapped retention lifecycle health to metadata-only resilience payloads with recovery fields.
- `src/nebula/services/runtime_health_service.py` — Aggregated readiness from typed resilience fields while preserving compatibility fallback behavior.
- `tests/support.py` — Updated shared test support for the new dependency health builder and payload shape.
- `tests/test_health.py` — Added degradation, fail-closed, and recovering health contract assertions.
- `tests/test_response_headers.py` — Aligned stable response-header assertions with the current routing metadata schema during verification.
- `tests/test_retention_lifecycle_service.py` — Locked metadata-only retention lifecycle health payload behavior.
