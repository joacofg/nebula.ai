---
id: T01
parent: S01
milestone: M010
key_files:
  - src/nebula/models/resilience.py
  - src/nebula/models/__init__.py
  - src/nebula/services/governance_store.py
  - src/nebula/services/semantic_cache_service.py
  - src/nebula/services/premium_provider_health_service.py
  - src/nebula/services/embeddings_service.py
  - src/nebula/services/retention_lifecycle_service.py
  - tests/support.py
  - tests/test_health.py
  - tests/test_retention_lifecycle_service.py
key_decisions:
  - Introduced a shared additive dependency health contract in `src/nebula/models/resilience.py` instead of duplicating ad hoc payload expansion in each service.
  - Mapped governance store to `serving_critical` + `fail_closed`, semantic cache/local Ollama/premium provider to `serving_optional` + `continuity_limited`, and retention lifecycle to `metadata_only` + `unaffected` while preserving legacy keys.
duration: 
verification_result: passed
completed_at: 2026-05-23T19:39:44.281Z
blocker_discovered: false
---

# T01: Added a shared resilience health contract and migrated dependency health producers to emit typed outage classification and recovery metadata.

**Added a shared resilience health contract and migrated dependency health producers to emit typed outage classification and recovery metadata.**

## What Happened

Added a new shared resilience contract module under `src/nebula/models/resilience.py` with typed dependency class, lifecycle state, serving effect, reason-code constants, ISO timestamp normalization, and a builder helper that preserves the existing `status`, `required`, and `detail` shape while adding machine-readable fields. Migrated `GovernanceStore.health_status()`, `SemanticCacheService.health_status()`, `PremiumProviderHealthService.health_status()`, `OllamaEmbeddingsService.health_status()`, and `RetentionLifecycleSnapshot.to_health_payload()` to emit the shared contract. Governance now reports serving-critical fail-closed readiness semantics; semantic cache, local Ollama, and premium provider report serving-optional continuity-limited semantics; retention lifecycle reports metadata-only unaffected semantics with recovery-state metadata. Updated shared test support and endpoint/service tests to assert the new additive fields without changing existing runtime surfaces.

## Verification

Verified the existing health endpoint suite still passes with additive resilience metadata and confirmed retention lifecycle health payloads expose metadata-only classification plus recovery-state fields.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `cd /Users/joaquinfernandezdegamboa/Proj/nebula && .venv/bin/pytest tests/test_health.py -q` | 0 | ✅ pass | 1155ms |
| 2 | `cd /Users/joaquinfernandezdegamboa/Proj/nebula && .venv/bin/pytest tests/test_retention_lifecycle_service.py -q` | 0 | ✅ pass | 1675ms |

## Deviations

Used the repo-local `.venv/bin/pytest` because `pytest` was not on PATH in the execution shell; verification scope was also extended with `tests/test_retention_lifecycle_service.py -q` to exercise the new metadata-only recovery fields.

## Known Issues

None.

## Files Created/Modified

- `src/nebula/models/resilience.py`
- `src/nebula/models/__init__.py`
- `src/nebula/services/governance_store.py`
- `src/nebula/services/semantic_cache_service.py`
- `src/nebula/services/premium_provider_health_service.py`
- `src/nebula/services/embeddings_service.py`
- `src/nebula/services/retention_lifecycle_service.py`
- `tests/support.py`
- `tests/test_health.py`
- `tests/test_retention_lifecycle_service.py`
