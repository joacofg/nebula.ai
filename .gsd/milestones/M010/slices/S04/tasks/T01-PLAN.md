---
estimated_steps: 1
estimated_files: 3
skills_used: []
---

# T01: Add deterministic recovery transition proofs for governance and semantic-cache outages

Why: S02 proved outage truth, but S04 owns the missing recovery leg: the same high-value dependency classes must recover cleanly without stale fail-closed or degraded claims lingering on existing health surfaces. Do: extend `tests/test_phase10_outage_safety.py` with stateful doubles or harness updates that exercise governance-store outage → recovery to successful serving and semantic-cache degraded outage → recovering/ready truth; add or tighten focused health-contract coverage in `tests/test_health.py` only if needed to lock the aggregate `recovering` semantics. Reuse existing deterministic support seams from `tests/support.py` and the additive payload builder from `src/nebula/models/resilience.py`; do not add network-chaos infrastructure or new endpoints. Done when: focused pytest coverage proves request behavior, `/health/ready`, and `/health/dependencies` all move truthfully across outage and recovery states for governance and semantic-cache paths, including explicit post-recovery evidence fields where applicable.

## Inputs

- `tests/test_phase10_outage_safety.py`
- `tests/test_health.py`
- `tests/support.py`
- `src/nebula/models/resilience.py`
- `src/nebula/services/runtime_health_service.py`
- `src/nebula/main.py`
- `.gsd/milestones/M010/slices/S02/S02-SUMMARY.md`
- `.gsd/milestones/M010/slices/S03/S03-SUMMARY.md`

## Expected Output

- `tests/test_phase10_outage_safety.py`
- `tests/test_health.py`
- `tests/support.py`

## Verification

.venv/bin/pytest tests/test_phase10_outage_safety.py tests/test_health.py -q

## Observability Impact

Adds executable proof that existing health surfaces show truthful recovery transitions instead of stale outage state; strengthens future-agent diagnosis by locking recovering/ready semantics in tests.
