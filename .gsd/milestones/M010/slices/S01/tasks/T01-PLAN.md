---
estimated_steps: 3
estimated_files: 7
skills_used: []
---

# T01: Add shared resilience contract types and migrate dependency health payloads

Why: S01 needs one authoritative backend vocabulary before outage proofs or UI wording can be trusted. Today dependency producers return ad hoc dictionaries with only `status`, `required`, and `detail`, which is too coarse for the milestone’s serving-critical, serving-optional, and metadata-only outage classes.

Do: Add a shared backend resilience contract module under `src/nebula/models/` that is serialization-friendly and additive to current payloads. Define typed fields for dependency class (`serving_critical`, `serving_optional`, `metadata_only`), lifecycle state (`ready`, `degraded`, `not_ready`, `recovering`), serving effect (`fail_closed`, `continuity_limited`, `unaffected`), and a machine-readable reason code plus optional last failure/last recovery timestamps and booleans needed for compatibility. Migrate `GovernanceStore.health_status()`, `SemanticCacheService.health_status()`, `PremiumProviderHealthService.health_status()`, `OllamaEmbeddingsService.health_status()`, and `RetentionLifecycleSnapshot.to_health_payload()` to emit the shared contract while preserving existing `status`, `required`, and `detail` keys for callers. Keep hosted metadata models unchanged in this slice.

Done when: all dependency health producers emit the shared typed fields with compatibility keys intact, and the contract clearly classifies governance store as serving-critical, semantic cache / local ollama / premium provider as serving-optional, and retention lifecycle as metadata-only or equivalent non-serving classification consistent with the milestone research.

## Inputs

- `src/nebula/services/governance_store.py`
- `src/nebula/services/semantic_cache_service.py`
- `src/nebula/services/premium_provider_health_service.py`
- `src/nebula/services/embeddings_service.py`
- `src/nebula/services/retention_lifecycle_service.py`
- `tests/support.py`

## Expected Output

- `src/nebula/models/resilience.py`
- `src/nebula/services/governance_store.py`
- `src/nebula/services/semantic_cache_service.py`
- `src/nebula/services/premium_provider_health_service.py`
- `src/nebula/services/embeddings_service.py`
- `src/nebula/services/retention_lifecycle_service.py`
- `tests/support.py`

## Verification

pytest tests/test_health.py -q

## Observability Impact

Adds machine-readable dependency classification, serving effect, and recovery metadata to existing health payloads without changing endpoint topology.
