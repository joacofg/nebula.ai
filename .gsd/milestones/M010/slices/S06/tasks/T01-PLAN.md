---
estimated_steps: 1
estimated_files: 5
skills_used: []
---

# T01: Add premium-provider and hosted-metadata outage proofs

Why: R087 explicitly names premium-provider and hosted metadata service outage classes, but M010 currently proves only governance and semantic-cache classes directly. Do: extend `tests/test_phase10_outage_safety.py` using the existing outage harnesses to add a premium-provider outage scenario that preserves healthy local serving while `/health/ready` remains non-503 and `/health/dependencies` reports `premium_provider` as serving-optional degraded continuity-limited with stable reason/detail. Also tighten or extend the existing hosted outage proof so it explicitly establishes metadata-only continuity semantics and non-authoritative truth on existing surfaces. Reuse current resilience payload helpers and keep the change test-first and bounded. Done when both outage classes are directly covered by deterministic tests and the focused outage safety suite passes.

## Inputs

- `.gsd/REQUIREMENTS.md`
- `tests/test_phase10_outage_safety.py`
- `tests/test_health.py`

## Expected Output

- `tests/test_phase10_outage_safety.py`

## Verification

.venv/bin/pytest tests/test_phase10_outage_safety.py tests/test_health.py -q

## Observability Impact

Produces explicit verification evidence for two previously under-proved outage classes on existing health truth surfaces.
