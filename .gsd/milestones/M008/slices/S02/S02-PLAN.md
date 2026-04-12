# S02: Governed ledger persistence and request markers

**Goal:** Make governed usage-ledger evidence age out through an explicit store lifecycle path while preserving historically truthful request markers until deletion and keeping operator inspection surfaces aligned with that behavior.
**Demo:** New requests persist only the allowed evidence shape for the tenant and carry per-request governance markers so request detail can later show what policy applied at write time.

## Must-Haves

- Expired usage-ledger rows are actually deleted using the persisted `evidence_expires_at` marker rather than current tenant policy inference.
- The existing admin ledger/read seams prove both sides of the contract: surviving rows still show write-time governance markers, and expired rows disappear after cleanup.
- Request-detail/operator copy stays consistent with the bounded evidence story and does not imply soft-delete, hidden retention, or hosted export expansion.

## Proof Level

- This slice proves: integration

## Integration Closure

`GovernanceStore.record_usage()` remains the sole write-time governance seam from S01, and this slice closes the next runtime leg by adding an explicit local cleanup lifecycle plus read-path verification through `/v1/admin/usage/ledger` and request-detail copy. After this slice, later milestone work can build richer operator explanation on top of a real persistence/deletion contract instead of inferred policy state.

## Verification

- Future agents can inspect governed evidence state through `usage_ledger` rows returned by `GovernanceStore.list_usage_records()` / `/v1/admin/usage/ledger`, and diagnose retention behavior from cleanup return counts plus the continued presence or absence of row-level governance markers (`evidence_retention_window`, `evidence_expires_at`, `metadata_fields_suppressed`, `governance_source`). Redaction remains unchanged: no raw prompts, responses, embeddings, provider credentials, or hosted raw ledger export are introduced.

## Tasks

- [x] **T01: Implement explicit ledger retention cleanup in the governance store** `est:1h`
  Add a store-level lifecycle path that deletes expired governed ledger rows based on the persisted `evidence_expires_at` marker, not the tenant’s current policy. Executors should load the `debug-like-expert` and `test` skills before coding.

Steps:
1. Extend `GovernanceStore` with an explicit cleanup method such as `delete_expired_usage_records(now=...)` that removes rows whose persisted `evidence_expires_at` is at or before the cleanup timestamp, ignores rows with no expiration marker, and returns a small deterministic summary/count suitable for diagnostics and tests.
2. Keep the write-time seam centralized: do not move governance logic into chat or embeddings writers, and preserve `record_usage()` / `_apply_usage_governance()` as the only place that stamps retention/minimization markers on new rows.
3. Add or update targeted backend tests in `tests/test_governance_api.py` that seed governed rows through existing app/store seams, prove surviving rows still expose historical markers before cleanup, prove expired rows are actually removed after cleanup, and prove a second cleanup pass is idempotent.
4. Re-run the chat and embeddings ledger tests that lock the shared persistence seam so cleanup work cannot regress message-type markers or per-request governance fields.

Assumption to document in code/tests: M008/S02 needs an explicit callable lifecycle seam and proof of actual deletion, but not a background scheduler yet.
  - Files: `src/nebula/services/governance_store.py`, `tests/test_governance_api.py`, `tests/test_chat_completions.py`, `tests/test_embeddings_api.py`
  - Verify: ./.venv/bin/pytest tests/test_governance_api.py -k "ledger or retention or expired" && ./.venv/bin/pytest tests/test_chat_completions.py -k ledger && ./.venv/bin/pytest tests/test_embeddings_api.py

- [ ] **T02: Align admin and request-detail surfaces with real evidence aging semantics** `est:45m`
  Carry the new retention lifecycle truth through the existing operator-facing read seams without inventing a new governance dashboard. Executors should load the `react-best-practices` and `test` skills before coding.

Steps:
1. If needed, expose a minimal admin/read-path seam that allows tests to prove cleanup effects through existing usage-ledger APIs rather than direct database inspection, keeping the surface local-authoritative and bounded.
2. Update request-detail and any mirrored admin types only as far as needed to explain that a persisted row is authoritative while it exists and may later disappear when governed retention cleanup deletes expired evidence. Do not imply soft-delete, archival recovery, or hosted raw export.
3. Add focused backend/UI verification covering the operator-facing contract: surviving rows still render persisted governance markers, and the request-detail copy remains consistent with actual deletion behavior introduced in T01.
4. Re-run the hosted-boundary regression suite to prove the slice did not widen the metadata-only export contract.

If no new backend route is necessary after T01, keep this task limited to read-path tests and UI/copy alignment rather than inventing extra API surface.
  - Files: `src/nebula/api/routes/admin.py`, `tests/test_governance_api.py`, `console/src/components/ledger/ledger-request-detail.tsx`, `console/src/components/ledger/ledger-request-detail.test.tsx`, `console/src/lib/admin-api.ts`, `tests/test_hosted_contract.py`
  - Verify: ./.venv/bin/pytest tests/test_governance_api.py -k "usage_ledger or retention" && ./.venv/bin/pytest tests/test_hosted_contract.py && npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx

## Files Likely Touched

- src/nebula/services/governance_store.py
- tests/test_governance_api.py
- tests/test_chat_completions.py
- tests/test_embeddings_api.py
- src/nebula/api/routes/admin.py
- console/src/components/ledger/ledger-request-detail.tsx
- console/src/components/ledger/ledger-request-detail.test.tsx
- console/src/lib/admin-api.ts
- tests/test_hosted_contract.py
