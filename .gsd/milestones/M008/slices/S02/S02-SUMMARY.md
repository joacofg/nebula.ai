---
id: S02
parent: M008
milestone: M008
provides:
  - A real local retention lifecycle seam for governed usage-ledger evidence.
  - Verified row-level historical governance markers that remain inspectable while a row exists.
  - A truthful operator explanation that expired evidence disappears after cleanup instead of being soft-deleted or exported elsewhere.
requires:
  - slice: S01
    provides: Typed tenant evidence-governance policy fields and write-time usage-ledger governance markers that this slice deletes and explains through persisted row-level markers.
affects:
  []
key_files:
  - src/nebula/services/governance_store.py
  - tests/test_governance_api.py
  - tests/test_chat_completions.py
  - tests/test_embeddings_api.py
  - console/src/components/ledger/ledger-request-detail.tsx
  - console/src/components/ledger/ledger-request-detail.test.tsx
  - console/src/lib/admin-api.ts
  - tests/test_hosted_contract.py
key_decisions:
  - Kept governance marker stamping centralized in `GovernanceStore.record_usage()` / `_apply_usage_governance()` and added retention cleanup as a separate explicit lifecycle seam.
  - Used the existing `/v1/admin/usage/ledger` seam as the authoritative operator read path for proving both surviving-row governance markers and expired-row disappearance rather than inventing a retention-specific endpoint.
  - Framed request detail as authoritative only while the persisted ledger row still exists, explicitly rejecting soft-delete, archive recovery, and hosted raw export semantics.
patterns_established:
  - For evidence-governance work, preserve one write-time seam for stamping row-level markers and add lifecycle behavior separately rather than re-spreading policy logic across writers.
  - When proving historical explainability, verify through the real operator read seam (`/v1/admin/usage/ledger` and request detail) instead of direct database inspection alone.
  - Prefer persisted row markers such as `evidence_expires_at` over current tenant policy inference for deletion and historical explanation semantics.
observability_surfaces:
  - `GovernanceStore.delete_expired_usage_records(now=...)` returns deterministic cleanup diagnostics (`eligible_count`, `deleted_count`, `cutoff`) suitable for tests and future operational hooks.
  - `/v1/admin/usage/ledger` remains the bounded read seam for confirming surviving-row markers and post-cleanup disappearance.
  - Request-detail evidence copy now communicates the truthful persistence/deletion boundary to operators.
drill_down_paths:
  - .gsd/milestones/M008/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M008/slices/S02/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-04-12T00:33:51.615Z
blocker_discovered: false
---

# S02: Governed ledger persistence and request markers

**Added explicit governed usage-ledger cleanup keyed by persisted evidence expiration markers, preserved write-time governance markers on surviving rows, and aligned request-detail/operator copy with real deletion semantics.**

## What Happened

S02 closed the next runtime leg of M008’s evidence-governance story without widening Nebula’s trust boundary. The slice kept `GovernanceStore.record_usage()` / `_apply_usage_governance()` as the sole write-time seam for stamping retention and minimization markers on new usage-ledger rows, then added an explicit lifecycle seam in `GovernanceStore.delete_expired_usage_records(now=...)` to delete only rows whose persisted `evidence_expires_at` is at or before the cleanup cutoff. That means retention cleanup now follows the historical marker written on the row, not the tenant’s current policy, which preserves truthful historical inspection while a row exists and prevents later policy edits from rewriting the evidence story.

Task execution proved both sides of the contract through the existing operator read seam instead of new API surface. Backend tests seeded governed rows through the normal runtime/store path, confirmed surviving rows still expose persisted governance markers such as `evidence_retention_window`, `evidence_expires_at`, `metadata_fields_suppressed`, and `governance_source`, confirmed rows with no expiration marker are ignored by cleanup, confirmed expired rows disappear from `/v1/admin/usage/ledger` after cleanup, and confirmed a second cleanup pass is idempotent. Chat and embeddings ledger tests revalidated that the shared persistence seam still stamps governed markers for both request families after the cleanup work landed.

On the operator-facing side, the slice deliberately stayed bounded to the existing request-detail and admin ledger surfaces. `ledger-request-detail` copy now explains that the persisted row is authoritative only while it still exists and that governed cleanup removes expired evidence rather than soft-deleting it, hiding it for later recovery, or exporting it to a hosted plane. Console types were tightened to mirror the backend governance fields already used in the ledger contract. The hosted metadata-only boundary was reverified unchanged, so the slice improves evidence governance and historical explainability without introducing raw prompt/response capture, raw ledger export, or hosted authority drift.

The main implementation assumption is explicit and now documented by the slice: M008/S02 needed a callable cleanup lifecycle seam and proof of actual deletion, but not a background scheduler yet. That operationalization remains for later milestone work.

## Verification

All slice-plan verification passed in the assembled worktree. Backend retention coverage passed with `./.venv/bin/pytest tests/test_governance_api.py -k "ledger or retention or expired"` (5 passed), proving explicit cleanup deletes expired rows by persisted `evidence_expires_at`, ignores rows with no expiration marker, and remains idempotent while surviving rows continue to expose historical governance markers. Shared persistence seam regressions were checked with `./.venv/bin/pytest tests/test_chat_completions.py -k ledger` (1 passed) and `./.venv/bin/pytest tests/test_embeddings_api.py` (5 passed), confirming governed chat and embeddings ledger writes still carry the expected request markers. Read-path and boundary verification passed with `./.venv/bin/pytest tests/test_governance_api.py -k "usage_ledger or retention"` (3 passed), `./.venv/bin/pytest tests/test_hosted_contract.py` (10 passed), and `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx` (15 passed), confirming admin ledger visibility, deletion semantics, request-detail copy alignment, and unchanged hosted metadata-only export behavior. Observability/diagnostic surfaces for this slice are the cleanup return summary plus `/v1/admin/usage/ledger` visibility before and after cleanup; both were exercised and behaved as expected.

## Requirements Advanced

- R062 — Advances the end-to-end governance proof by closing the persistence-to-deletion runtime leg and keeping operator read seams aligned with actual cleanup behavior.
- R063 — Improves operator trust by preserving useful request-level governance evidence while the row exists and by making deletion semantics explicit rather than ambiguous.
- R064 — Keeps the milestone bounded by reusing existing ledger and request-detail surfaces instead of expanding into a compliance dashboard, archive system, or hosted authority surface.

## Requirements Validated

- R058 — Passing backend, hosted-boundary, and console verification proves request evidence remains historically explainable through persisted row-level governance markers while the row exists, and that later cleanup truthfully removes expired evidence by persisted expiration rather than current-policy inference.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

No new backend route was added. The existing `/v1/admin/usage/ledger` seam already provided the bounded operator read path needed to prove surviving-row visibility and expired-row disappearance, so the slice stayed focused on lifecycle cleanup, read-path verification, and request-detail copy alignment. One small TypeScript adaptation was made in `console/src/lib/admin-api.ts` to add literal aliases already referenced by the mirrored usage-ledger types.

## Known Limitations

This slice adds an explicit callable cleanup lifecycle seam but does not schedule or automate cleanup execution yet. Operators and tests can prove actual deletion behavior now, but ongoing retention execution policy, cadence, and operational triggering remain future work. Historical request detail is truthful only while the row exists; once cleanup deletes it, there is intentionally no soft-delete or recovery surface.

## Follow-ups

S03 should operationalize the cleanup lifecycle beyond the callable store seam and define how retention execution is triggered, monitored, and recovered if it fails. S04 should continue the operator explanation work by making the effective evidence boundary and post-deletion absence more legible in the console. S05 should assemble the full end-to-end proof path from tenant policy to persistence to deletion to operator inspection while keeping the hosted plane metadata-only.

## Files Created/Modified

- `src/nebula/services/governance_store.py` — Added explicit `delete_expired_usage_records(now=...)` lifecycle cleanup keyed by persisted `evidence_expires_at`.
- `tests/test_governance_api.py` — Added end-to-end retention cleanup coverage through the real admin ledger seam, including surviving-marker visibility, expired-row disappearance, no-expiration preservation, and idempotent cleanup.
- `tests/test_chat_completions.py` — Reverified shared governed chat ledger persistence after cleanup work to ensure request markers still stamp correctly.
- `tests/test_embeddings_api.py` — Reverified shared governed embeddings ledger persistence after cleanup work to ensure request markers still stamp correctly.
- `console/src/components/ledger/ledger-request-detail.tsx` — Updated request-detail copy to explain that persisted evidence is authoritative only while the row exists and may disappear after governed cleanup.
- `console/src/components/ledger/ledger-request-detail.test.tsx` — Locked the new request-detail evidence-aging semantics with focused UI assertions.
- `console/src/lib/admin-api.ts` — Added missing evidence-governance literal aliases to keep the mirrored admin usage-ledger contract types aligned with backend fields.
- `tests/test_hosted_contract.py` — Reverified that hosted export remains metadata-only after the retention-lifecycle and request-detail changes.
