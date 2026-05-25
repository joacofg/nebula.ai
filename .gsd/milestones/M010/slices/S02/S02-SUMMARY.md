---
id: S02
parent: M010
milestone: M010
provides:
  - Concrete outage-path evidence for one serving-critical and one serving-optional dependency class.
  - Verified request-behavior-to-health-surface alignment for downstream operator-visibility and recovery slices.
requires:
  - slice: S01
    provides: Typed resilience contract and runtime health vocabulary for serving-critical versus serving-optional dependencies.
affects:
  - S03
  - S04
  - S05
key_files:
  - tests/test_phase10_outage_safety.py
  - tests/test_health.py
  - tests/support.py
  - src/nebula/services/auth_service.py
key_decisions:
  - Governance-store outages on the auth path must be bounded into a 503 fail-closed response so request truth matches readiness and dependency health.
  - Serving-optional outage tests should preserve production fallback semantics and typed health payloads instead of injecting uncaught exceptions that bypass graceful degradation.
patterns_established:
  - End-to-end resilience tests should exercise real request paths with deterministic doubles that preserve production degradation behavior.
  - Existing `/health/ready` and `/health/dependencies` surfaces remain the authoritative proof surfaces for outage truth, rather than adding resilience-specific APIs.
observability_surfaces:
  - `/health/ready` overall readiness status and HTTP 503 signaling for serving-critical outages.
  - `/health/dependencies` typed dependency entries showing class, lifecycle, serving effect, and reason-code evidence for governance and semantic-cache outages.
drill_down_paths:
  - .gsd/milestones/M010/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M010/slices/S02/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-05-23T19:57:56.642Z
blocker_discovered: false
---

# S02: S02

**Verified end-to-end outage proofs for one serving-critical and one serving-optional dependency class, confirming fail-closed versus degraded-serving runtime behavior and matching health-surface truth.**

## What Happened

S02 closed the gap between the typed resilience contract from S01 and real outage-path runtime behavior. T01 added a deterministic governance-store outage proof on the real request path and exposed that governance access failures could occur during tenant-context resolution in AuthService before chat orchestration. The task work introduced the smallest backend fix there so unexpected governance-store access failures are converted into a bounded 503 "Governance store unavailable." fail-closed response rather than surfacing as raw runtime errors, while the same outage also drives `/health/ready` to 503/not_ready and `/health/dependencies` to a serving-critical `governance_store` entry with fail-closed semantics. T02 added the complementary serving-optional proof for semantic-cache degradation. The test support and focused outage/health tests now emulate production cache fallback semantics so chat completions still succeed through the existing local path while `/health/ready` remains non-503 and `/health/dependencies` reports `semantic_cache` as degraded with continuity-limited truth. Together the slice now provides downstream slices with concrete outage evidence showing Nebula fails closed for serving-critical governance outages, degrades truthfully for serving-optional semantic-cache outages, and keeps existing health surfaces authoritative for operator inspection.

## Verification

Ran `.venv/bin/pytest tests/test_phase10_outage_safety.py tests/test_health.py -q` via `gsd_exec` and confirmed `10 passed in 1.77s`. This fresh slice-level verification proves both outage classes on the current worktree: governance outage requests fail with bounded non-200 semantics while readiness returns 503 and dependency health reports serving-critical fail-closed truth; semantic-cache outage requests still return 200 while readiness stays non-503 and dependency health reports serving-optional degraded continuity-limited truth.

## Requirements Advanced

- R086 — Added verified runtime outage behavior proof covering fail-closed and degraded-serving paths on existing health surfaces.
- R087 — Proved dependency-specific degraded behavior for governance-store and semantic-cache outages with truthful response semantics.
- R088 — Provided concrete health-surface evidence that operators can inspect during serving-critical and serving-optional outages.

## Requirements Validated

- R087 — Fresh slice verification passed with deterministic governance fail-closed and semantic-cache degraded-serving outage scenarios plus matching readiness/dependency payload truth.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Operational Readiness

None.

## Deviations

T01 required a minimal backend fix in `src/nebula/services/auth_service.py` because the new governance outage proof surfaced an unbounded exception path during tenant-context resolution; T02 required aligning cache doubles with production fallback semantics and the typed health payload contract.

## Known Limitations

Verification is deterministic and test-harness-based rather than driven by live dependency containers or network fault injection. Operator-surface presentation and recovery proof remain for S03 and S04.

## Follow-ups

S03 should reuse these concrete governance and semantic-cache outage examples when validating operator-visible resilience state on existing surfaces. S04 should build recovery verification on the same failure-state transitions and reason-code evidence proved here.

## Files Created/Modified

- `tests/test_phase10_outage_safety.py` — Added end-to-end governance-store and semantic-cache outage proofs covering request behavior and health truth.
- `tests/test_health.py` — Added focused degraded semantic-cache health contract regression coverage.
- `tests/support.py` — Expanded outage test doubles to express degraded cache health while preserving serving continuity.
- `src/nebula/services/auth_service.py` — Mapped unexpected governance-store access failures during auth/tenant resolution to a bounded 503 fail-closed response.
