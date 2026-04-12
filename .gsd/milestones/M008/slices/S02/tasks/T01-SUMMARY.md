---
id: T01
parent: S02
milestone: M008
key_files:
  - src/nebula/services/governance_store.py
  - tests/test_governance_api.py
key_decisions:
  - Kept governance marker stamping centralized in `record_usage()` / `_apply_usage_governance()` and implemented retention cleanup as a separate store lifecycle seam.
  - Used direct model insertion only inside the test to create a row with no persisted expiration marker, because routing it through `record_usage()` would correctly restamp governance fields and invalidate the edge-case fixture.
duration: 
verification_result: passed
completed_at: 2026-04-12T00:28:50.097Z
blocker_discovered: false
---

# T01: Added explicit governance-store cleanup for expired usage ledger rows with retention lifecycle coverage tests.

**Added explicit governance-store cleanup for expired usage ledger rows with retention lifecycle coverage tests.**

## What Happened

Implemented a store-level retention lifecycle seam in `src/nebula/services/governance_store.py:363` by adding `delete_expired_usage_records(now=...)`, which deletes only rows whose persisted `evidence_expires_at` is at or before the supplied cutoff, ignores rows with no expiration marker, and returns a deterministic diagnostic summary (`eligible_count`, `deleted_count`, `cutoff`). I kept the write-time governance seam centralized in `record_usage()` / `_apply_usage_governance()` and did not move policy stamping into chat or embeddings writers. In `tests/test_governance_api.py:495` I added an end-to-end retention test that seeds governed rows through the normal request path, verifies historical governance markers remain visible before cleanup, proves expired rows disappear after cleanup, proves rows without a persisted expiration marker survive cleanup, and proves a second cleanup pass is idempotent. During verification I found that re-seeding through `record_usage()` correctly reapplies governance markers, so I adjusted the null-expiration fixture to be inserted directly at the model layer in the test to preserve the central write seam while still exercising the cleanup edge case. I also normalized cutoff assertions to account for SQLite timezone representation while still validating the same cleanup instant semantically.

## Verification

Ran the slice verification command set. `./.venv/bin/pytest tests/test_governance_api.py -k "ledger or retention or expired"` passed and covered the new cleanup behavior plus governed ledger marker visibility. `./.venv/bin/pytest tests/test_chat_completions.py -k ledger` passed, confirming chat ledger persistence still stamps the expected governed message markers through the shared seam. `./.venv/bin/pytest tests/test_embeddings_api.py` passed, confirming embeddings ledger persistence still stamps the expected governed message markers and cleanup work did not regress the shared persistence path. I also directly verified the new observability seam through the cleanup test by asserting the returned deleted-row counts and post-cleanup row absence/presence via `/v1/admin/usage/ledger`.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_governance_api.py -k "ledger or retention or expired"` | 0 | ✅ pass | 870ms |
| 2 | `./.venv/bin/pytest tests/test_chat_completions.py -k ledger` | 0 | ✅ pass | 600ms |
| 3 | `./.venv/bin/pytest tests/test_embeddings_api.py` | 0 | ✅ pass | 870ms |

## Deviations

None.

## Known Issues

A non-essential helper command using `python` instead of `./.venv/bin/python` failed during file-line lookup; this did not affect implementation or verification.

## Files Created/Modified

- `src/nebula/services/governance_store.py`
- `tests/test_governance_api.py`
