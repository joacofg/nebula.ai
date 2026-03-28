---
estimated_steps: 24
estimated_files: 6
skills_used: []
---

# T01: Add recommendation and cache-summary backend contracts

Why: S04 depends on a narrow, deterministic backend seam that turns existing ledger, simulation, hard-budget, and runtime-cache facts into bounded operator guidance before any API or UI work can stay honest.

Steps:
1. Extend `src/nebula/models/governance.py` with typed recommendation and cache-summary DTOs plus any minimal tenant policy fields required for cache tuning, keeping the response bounded and operator-readable.
2. Implement `src/nebula/services/recommendation_service.py` to derive tenant-scoped recommendations and cache insights from `list_usage_records(...)`, hard-budget/policy outcomes, cache-hit history, avoided premium-cost estimates, and runtime cache health without writing policies, usage rows, or cache data.
3. Wire the new service through `src/nebula/core/container.py` and add focused service tests in `tests/test_service_flows.py` for deterministic recommendation ordering, bounded output, degraded-cache insight behavior, and no-mutation guarantees.

Must-haves:
- Introduce stable DTOs for recommendation cards and cache insight summaries rather than free-form dicts.
- Keep recommendation logic ledger-backed and scope-disciplined under R044; do not depend on raw prompt text, opaque scoring, or Qdrant entry inspection.
- If cache tuning needs more than `semantic_cache_enabled`, add only the smallest explicit policy knobs needed and carry them through the shared model contract here.

Verification:
- `./.venv/bin/pytest tests/test_service_flows.py -k "recommendation or cache" -x`
- Service tests prove bounded recommendation/cache output, degraded-health visibility, and zero policy/usage mutation side effects.

Inputs:
- `src/nebula/models/governance.py`
- `src/nebula/services/governance_store.py`
- `src/nebula/services/semantic_cache_service.py`
- `src/nebula/services/policy_simulation_service.py`
- `src/nebula/core/container.py`
- `tests/test_service_flows.py`

Expected output:
- `src/nebula/models/governance.py`
- `src/nebula/services/recommendation_service.py`
- `src/nebula/core/container.py`
- `tests/test_service_flows.py`

## Inputs

- ``src/nebula/models/governance.py``
- ``src/nebula/services/governance_store.py``
- ``src/nebula/services/semantic_cache_service.py``
- ``src/nebula/services/policy_simulation_service.py``
- ``src/nebula/core/container.py``
- ``tests/test_service_flows.py``

## Expected Output

- ``src/nebula/models/governance.py``
- ``src/nebula/services/recommendation_service.py``
- ``src/nebula/core/container.py``
- ``tests/test_service_flows.py``

## Verification

./.venv/bin/pytest tests/test_service_flows.py -k "recommendation or cache" -x

## Observability Impact

Adds a typed recommendation/cache-summary inspection surface and makes degraded semantic-cache state visible to downstream API/UI consumers.
