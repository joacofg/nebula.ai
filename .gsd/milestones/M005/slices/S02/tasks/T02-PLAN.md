---
estimated_steps: 1
estimated_files: 4
skills_used: []
---

# T02: Expose tenant policy simulation through the admin API

Add a new admin route such as `POST /v1/admin/tenants/{tenant_id}/policy/simulate` in `src/nebula/api/routes/admin.py`, colocated with existing policy CRUD routes. Reuse the T01 DTOs so the endpoint accepts a candidate `TenantPolicy` plus bounded replay filters and returns the full simulation summary without persisting anything. Keep tenant existence checks, filter validation, and bounded result sizing explicit at the route boundary, and add focused API tests in `tests/test_governance_api.py` that prove tenant scoping, aggregate replay output, newly denied detection, unchanged/empty result handling, and that saved tenant policy remains unchanged after simulation calls.

## Inputs

- ``src/nebula/api/routes/admin.py``
- ``src/nebula/models/governance.py``
- ``src/nebula/services/policy_simulation_service.py``
- ``tests/test_governance_api.py``

## Expected Output

- ``src/nebula/api/routes/admin.py``
- ``src/nebula/models/governance.py``
- ``tests/test_governance_api.py``

## Verification

./.venv/bin/pytest tests/test_governance_api.py -k simulation -x

## Observability Impact

- Signals added/changed: the admin API becomes the canonical inspection surface for simulation summaries and changed-request samples.
- How a future agent inspects this: run `./.venv/bin/pytest tests/test_governance_api.py -k simulation -x` and call the endpoint with tenant/window filters.
- Failure state exposed: 404 tenant errors, validation failures, and replay-service errors are surfaced as explicit API responses instead of silent empty payloads.
