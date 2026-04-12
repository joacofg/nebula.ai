# S01: Typed evidence governance policy

**Goal:** Establish a typed evidence-governance contract across tenant policy, admin APIs, and persisted ledger rows so evidence retention and metadata minimization become runtime-enforced backend behavior with operator-visible policy controls and historically truthful request markers.
**Demo:** Operators can configure explicit tenant evidence-retention and metadata-minimization policy through the existing policy boundary, and backend/admin contracts treat those controls as runtime-enforced rather than advisory.

## Must-Haves

- Tenant policy, admin policy options, and mirrored console types expose explicit runtime-enforced fields for evidence retention and metadata minimization without widening into raw prompt/response capture.
- Chat and embeddings ledger writes both pass through a single governed persistence seam that suppresses non-essential metadata according to policy and stamps each row with request-time governance markers.
- The existing operator policy surface can edit the new governance fields and the request-detail surface remains compatible with the governed ledger contract, while hosted metadata-only tests still prove no trust-boundary widening.

## Proof Level

- This slice proves: integration

## Integration Closure

This slice closes the backend contract and operator policy wiring for evidence governance, including request-time row markers that later slices will explain more deeply. Remaining milestone work is retention execution/deletion proof and richer request-detail/operator explanation built on the markers established here.

## Verification

- Governed persistence must leave future agents with clear inspection points: admin policy/options responses, usage-ledger rows, and targeted tests that prove which fields were suppressed or preserved for chat and embeddings writes. Verification should make it obvious whether a failure is schema drift, policy classification drift, or record-transformation drift.

## Tasks

- [x] **T01: Add typed evidence governance schema and backend persistence contract** `est:5h`
  Implement the backend-first contract that S01 owns directly for R056 and R057 and supports for R062/R064. Extend the canonical governance models, SQLAlchemy models, and a new additive Alembic migration with explicit evidence-retention and metadata-minimization fields plus row-level governance markers on `usage_ledger`. Centralize request-time governance transformation in `GovernanceStore.record_usage()` so both chat and embeddings can share one enforcement seam, and update the admin policy/options API classification to mark the new controls as runtime-enforced rather than advisory. Cover the new contract with targeted backend tests that prove policy CRUD, policy-options classification, and governed ledger persistence behavior without widening hosted export scope.

Assumption to document in code/tests: S01 establishes typed retention policy and persisted expiration/minimization markers now, but actual deletion execution remains for S03.
  - Files: `src/nebula/models/governance.py`, `src/nebula/db/models.py`, `migrations/versions/20260411_0010_evidence_governance_policy.py`, `src/nebula/services/governance_store.py`, `src/nebula/api/routes/admin.py`, `tests/test_governance_api.py`, `tests/test_service_flows.py`, `tests/test_hosted_contract.py`
  - Verify: pytest tests/test_governance_api.py tests/test_service_flows.py tests/test_hosted_contract.py

- [ ] **T02: Wire chat, embeddings, and console policy surfaces to the governed evidence contract** `est:5h`
  Finish the slice by threading the typed governance fields through the live request writers and operator-facing policy boundary. Update chat and embeddings usage recording to populate the new row markers through the centralized store contract, mirror the backend type changes in the console admin client, and add bounded policy-form/policy-page UI controls plus copy that present evidence governance as runtime-enforced tenant controls rather than deferred advisory capture settings. Keep request-detail changes minimal but sufficient to stay type-compatible with the new ledger row shape and preserve space for later slices to explain those markers. Add backend and Vitest coverage proving the full S01 demo path: operator-configured policy reaches backend contracts, chat and embeddings ledger rows persist governed markers/minimized metadata, and the operator policy surface exposes the controls truthfully.
  - Files: `src/nebula/services/chat_service.py`, `src/nebula/api/routes/embeddings.py`, `console/src/lib/admin-api.ts`, `console/src/components/policy/policy-form.tsx`, `console/src/components/policy/policy-advanced-section.tsx`, `console/src/components/ledger/ledger-request-detail.tsx`, `tests/test_chat_completions.py`, `tests/test_embeddings_api.py`, `console/src/components/policy/policy-form.test.tsx`, `console/src/components/policy/policy-page.test.tsx`, `console/src/components/ledger/ledger-request-detail.test.tsx`
  - Verify: pytest tests/test_chat_completions.py -k ledger && pytest tests/test_embeddings_api.py && npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx

## Files Likely Touched

- src/nebula/models/governance.py
- src/nebula/db/models.py
- migrations/versions/20260411_0010_evidence_governance_policy.py
- src/nebula/services/governance_store.py
- src/nebula/api/routes/admin.py
- tests/test_governance_api.py
- tests/test_service_flows.py
- tests/test_hosted_contract.py
- src/nebula/services/chat_service.py
- src/nebula/api/routes/embeddings.py
- console/src/lib/admin-api.ts
- console/src/components/policy/policy-form.tsx
- console/src/components/policy/policy-advanced-section.tsx
- console/src/components/ledger/ledger-request-detail.tsx
- tests/test_chat_completions.py
- tests/test_embeddings_api.py
- console/src/components/policy/policy-form.test.tsx
- console/src/components/policy/policy-page.test.tsx
- console/src/components/ledger/ledger-request-detail.test.tsx
