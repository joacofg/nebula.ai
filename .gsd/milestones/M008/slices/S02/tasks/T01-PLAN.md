---
estimated_steps: 7
estimated_files: 4
skills_used: []
---

# T01: Implement explicit ledger retention cleanup in the governance store

Add a store-level lifecycle path that deletes expired governed ledger rows based on the persisted `evidence_expires_at` marker, not the tenant’s current policy. Executors should load the `debug-like-expert` and `test` skills before coding.

Steps:
1. Extend `GovernanceStore` with an explicit cleanup method such as `delete_expired_usage_records(now=...)` that removes rows whose persisted `evidence_expires_at` is at or before the cleanup timestamp, ignores rows with no expiration marker, and returns a small deterministic summary/count suitable for diagnostics and tests.
2. Keep the write-time seam centralized: do not move governance logic into chat or embeddings writers, and preserve `record_usage()` / `_apply_usage_governance()` as the only place that stamps retention/minimization markers on new rows.
3. Add or update targeted backend tests in `tests/test_governance_api.py` that seed governed rows through existing app/store seams, prove surviving rows still expose historical markers before cleanup, prove expired rows are actually removed after cleanup, and prove a second cleanup pass is idempotent.
4. Re-run the chat and embeddings ledger tests that lock the shared persistence seam so cleanup work cannot regress message-type markers or per-request governance fields.

Assumption to document in code/tests: M008/S02 needs an explicit callable lifecycle seam and proof of actual deletion, but not a background scheduler yet.

## Inputs

- ``src/nebula/services/governance_store.py``
- ``src/nebula/models/governance.py``
- ``src/nebula/db/models.py``
- ``tests/test_governance_api.py``
- ``tests/test_chat_completions.py``
- ``tests/test_embeddings_api.py``

## Expected Output

- ``src/nebula/services/governance_store.py``
- ``tests/test_governance_api.py``

## Verification

./.venv/bin/pytest tests/test_governance_api.py -k "ledger or retention or expired" && ./.venv/bin/pytest tests/test_chat_completions.py -k ledger && ./.venv/bin/pytest tests/test_embeddings_api.py

## Observability Impact

Adds an explicit diagnostic seam for retention lifecycle behavior: the cleanup method’s deleted-row count plus post-cleanup absence from `/v1/admin/usage/ledger` give future agents a bounded way to confirm whether a row expired, was deleted, or never matched cleanup criteria.
