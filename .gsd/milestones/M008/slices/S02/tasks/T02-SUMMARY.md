---
id: T02
parent: S02
milestone: M008
key_files:
  - tests/test_governance_api.py
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/ledger/ledger-request-detail.test.tsx
  - console/src/lib/admin-api.ts
key_decisions:
  - Kept the operator inspection path anchored on the existing `/v1/admin/usage/ledger` seam instead of inventing a new retention-specific endpoint.
  - Expressed evidence aging as row disappearance after governed cleanup, not soft-delete or hosted export expansion, so request detail remains truthful only while a persisted row exists.
duration: 
verification_result: passed
completed_at: 2026-04-12T00:31:46.745Z
blocker_discovered: false
---

# T02: Aligned admin ledger tests and request-detail copy with governed evidence aging semantics.

**Aligned admin ledger tests and request-detail copy with governed evidence aging semantics.**

## What Happened

Updated the operator-facing contract without adding new API surface because `/v1/admin/usage/ledger` already provided the bounded read seam needed to prove retention behavior. In `tests/test_governance_api.py` I extended the governed cleanup regression so it verifies cleanup effects through the admin ledger endpoint itself: the expired request disappears from the tenant ledger listing after cleanup, while surviving and no-expiration rows remain visible with their persisted governance markers. In `console/src/components/ledger/ledger-request-detail.tsx` I revised the request-detail explanation to state that a persisted row is authoritative only while it still exists and that governed cleanup removes the detail surface instead of implying soft-delete, archive recovery, or hosted raw export. In `console/src/components/ledger/ledger-request-detail.test.tsx` I updated the UI assertions to cover that copy precisely. I also fixed a local TypeScript mismatch in `console/src/lib/admin-api.ts` by defining the `EvidenceRetentionWindow` and `MetadataMinimizationLevel` literal types already referenced by `UsageLedgerRecord`, keeping the mirrored admin types aligned with backend governance fields.

## Verification

Ran the task verification commands directly. `./.venv/bin/pytest tests/test_governance_api.py -k "usage_ledger or retention"` passed, including the strengthened admin-ledger cleanup proof that surviving rows retain persisted governance markers and expired rows disappear from `/v1/admin/usage/ledger` after cleanup. `./.venv/bin/pytest tests/test_hosted_contract.py` passed, confirming the metadata-only hosted export boundary did not widen. `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx` passed after tightening the UI assertion to validate the new explanatory copy rather than incorrectly rejecting the words used in the warning itself.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_governance_api.py -k "usage_ledger or retention"` | 0 | ✅ pass | 930ms |
| 2 | `./.venv/bin/pytest tests/test_hosted_contract.py` | 0 | ✅ pass | 40ms |
| 3 | `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx` | 0 | ✅ pass | 525ms |

## Deviations

No backend route changes were needed after verifying the existing admin ledger endpoint already satisfied the planned read-path seam. I made one small local adaptation outside the expected-output list by adding missing TypeScript literal aliases in `console/src/lib/admin-api.ts`, because the request-detail types already referenced them and keeping the mirrored admin types accurate was necessary for consistency.

## Known Issues

None.

## Files Created/Modified

- `tests/test_governance_api.py`
- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`
- `console/src/lib/admin-api.ts`
