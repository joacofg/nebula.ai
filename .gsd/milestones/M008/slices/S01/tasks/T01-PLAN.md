---
estimated_steps: 2
estimated_files: 8
skills_used: []
---

# T01: Add typed evidence governance schema and backend persistence contract

Implement the backend-first contract that S01 owns directly for R056 and R057 and supports for R062/R064. Extend the canonical governance models, SQLAlchemy models, and a new additive Alembic migration with explicit evidence-retention and metadata-minimization fields plus row-level governance markers on `usage_ledger`. Centralize request-time governance transformation in `GovernanceStore.record_usage()` so both chat and embeddings can share one enforcement seam, and update the admin policy/options API classification to mark the new controls as runtime-enforced rather than advisory. Cover the new contract with targeted backend tests that prove policy CRUD, policy-options classification, and governed ledger persistence behavior without widening hosted export scope.

Assumption to document in code/tests: S01 establishes typed retention policy and persisted expiration/minimization markers now, but actual deletion execution remains for S03.

## Inputs

- `src/nebula/models/governance.py`
- `src/nebula/db/models.py`
- `src/nebula/services/governance_store.py`
- `src/nebula/api/routes/admin.py`
- `migrations/versions/20260401_0009_calibrated_routing_rollout.py`
- `tests/test_governance_api.py`
- `tests/test_service_flows.py`
- `tests/test_hosted_contract.py`

## Expected Output

- `src/nebula/models/governance.py`
- `src/nebula/db/models.py`
- `migrations/versions/20260411_0010_evidence_governance_policy.py`
- `src/nebula/services/governance_store.py`
- `src/nebula/api/routes/admin.py`
- `tests/test_governance_api.py`
- `tests/test_service_flows.py`
- `tests/test_hosted_contract.py`

## Verification

pytest tests/test_governance_api.py tests/test_service_flows.py tests/test_hosted_contract.py

## Observability Impact

Changes the canonical policy/options and ledger inspection surfaces. Future agents should be able to inspect governed state through `/v1/admin/policy/options`, `/v1/admin/usage/ledger`, and focused store tests that assert persisted governance markers and suppressed route metadata.
