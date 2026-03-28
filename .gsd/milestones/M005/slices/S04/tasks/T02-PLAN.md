---
estimated_steps: 23
estimated_files: 5
skills_used: []
---

# T02: Expose tenant recommendation API and console contracts

Why: Once the backend derivation seam exists, S04 needs one narrow admin contract and shared frontend typings so Observability and policy surfaces can consume the same tenant-scoped evidence without duplicating heuristics.

Steps:
1. Add tenant-scoped admin endpoint wiring in `src/nebula/api/routes/admin.py` for the compact recommendation/cache summary response, including tenant existence checks and admin-only protection.
2. Extend `console/src/lib/admin-api.ts` with the new response types and fetch helper, reusing the shared typed contract instead of ad-hoc UI parsing.
3. Add focused API tests in `tests/test_governance_api.py` for auth, 404 handling, bounded response structure, tenant scoping, and degraded-cache evidence propagation.

Must-haves:
- Keep the API surface narrow: one compact read path for tenant recommendations/cache insight unless tests prove a second endpoint is necessary.
- Preserve admin-only and tenant-scoped semantics with explicit 404 behavior for missing tenants.
- Ensure the response stays bounded and deterministic enough for UI rendering and future S05 proof work.

Verification:
- `./.venv/bin/pytest tests/test_governance_api.py -k "recommendation or cache" -x`
- API tests prove admin protection, tenant scoping, bounded structure, and degraded-cache evidence behavior.

Inputs:
- `src/nebula/api/routes/admin.py`
- `src/nebula/models/governance.py`
- `src/nebula/core/container.py`
- `console/src/lib/admin-api.ts`
- `tests/test_governance_api.py`
- `tests/test_service_flows.py`

Expected output:
- `src/nebula/api/routes/admin.py`
- `console/src/lib/admin-api.ts`
- `tests/test_governance_api.py`

## Inputs

- ``src/nebula/api/routes/admin.py``
- ``src/nebula/models/governance.py``
- ``src/nebula/core/container.py``
- ``console/src/lib/admin-api.ts``
- ``tests/test_governance_api.py``
- ``tests/test_service_flows.py``

## Expected Output

- ``src/nebula/api/routes/admin.py``
- ``console/src/lib/admin-api.ts``
- ``tests/test_governance_api.py``

## Verification

./.venv/bin/pytest tests/test_governance_api.py -k "recommendation or cache" -x

## Observability Impact

Makes tenant-scoped recommendation/cache evidence inspectable through a stable admin API surface that future agents can query directly during failures.
