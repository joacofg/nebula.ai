# S02 — Research

**Date:** 2026-04-11

## Summary

S02 is a **light-to-targeted research** slice. The core backend contract for governed evidence persistence is already in place from S01: tenant policy now carries `evidence_retention_window` and `metadata_minimization_level`, `GovernanceStore.record_usage()` centralizes write-time governance, and every `UsageLedgerRecord` already persists request-time governance markers (`message_type`, `evidence_expires_at`, `metadata_fields_suppressed`, `governance_source`). This directly supports **R058** and partially supports **R060/R062**; the remaining missing behavior is the second half of the trust claim from context: **real retention deletion** plus a request-detail/read-path story that stays historically truthful when rows are gone or policies later change.

The natural implementation seam is still `src/nebula/services/governance_store.py`. S01 established the correct pattern: enforce governance once at the ledger boundary and let chat, embeddings, admin API, and console read typed records. For S02, the safest move is to add explicit store-level retention operations that delete expired ledger rows based on the persisted `evidence_expires_at` marker, expose a bounded way to run/verify that cleanup through existing backend seams, and add tests proving operators can trust row-level markers before deletion and trust actual absence after deletion. Per the milestone context, this should stay request-led and local-authoritative, not turn into a dashboard or hosted feature.

## Recommendation

Implement S02 as a **store-first retention lifecycle pass** in `GovernanceStore`, then prove it through admin/read-path and request-detail-facing tests.

Why this approach:
- It follows the S01 forward-intelligence rule: keep evidence governance centralized in `GovernanceStore.record_usage()` / ledger seams so chat and embeddings cannot drift.
- The milestone context explicitly says the clean seam should be an **explicit governed-store lifecycle path**, not a hand-waved external/manual process.
- `UsageLedgerModel.evidence_expires_at` is already persisted, so retention deletion can be based on historical write-time truth instead of current policy inference.
- The hosted boundary remains untouched because `src/nebula/models/hosted_contract.py` already excludes `raw_usage_ledger_rows`; retention should operate locally only.

Reference from loaded skills that applies here: the installed **react-best-practices** / Next.js guidance is not the main driver for this slice; the more relevant rule is the project’s own established pattern from S01 plus the repo instruction to keep work bounded and request-led. This slice is primarily backend/store verification work, with only bounded read-surface compatibility implications.

## Implementation Landscape

### Key Files

- `src/nebula/services/governance_store.py` — authoritative persistence seam. Already applies policy in `_apply_usage_governance()` and exposes `record_usage()` / `list_usage_records()`. Best place to add retention cleanup, expired-row deletion queries, and any small helper like `delete_expired_usage_records(now=...)` or equivalent.
- `src/nebula/models/governance.py` — typed ledger contract. `UsageLedgerRecord` already includes `message_type`, `evidence_retention_window`, `evidence_expires_at`, `metadata_minimization_level`, `metadata_fields_suppressed`, and `governance_source`. If S02 needs an explicit read-time marker for deletion outcomes, add it here only if strictly necessary; prefer proving deletion by absence first.
- `src/nebula/db/models.py` — `UsageLedgerModel` already has the persisted columns needed for cleanup (`evidence_expires_at`, governance marker columns). No new schema is obviously required unless S02 decides deletion observability needs a durable audit marker; context suggests avoiding extra platform sprawl.
- `migrations/versions/20260411_0010_evidence_governance_policy.py` — confirms S01 already migrated the needed columns. Likely no new migration unless S02 introduces new persisted lifecycle fields.
- `src/nebula/api/routes/admin.py` — existing `GET /v1/admin/usage/ledger` read seam. If S02 needs an explicit bounded operator/admin cleanup trigger or filter behavior for deletion verification, it should be added here rather than inventing a parallel surface.
- `src/nebula/services/chat_service.py` — chat writer already records usage through `governance_store.record_usage(...)`. No new governance logic should be added here; only touch if tests need stronger request correlation proof.
- `src/nebula/api/routes/embeddings.py` — embeddings writer already records through the same store seam and generates fallback request IDs. Same guidance as chat: do not fork governance logic.
- `console/src/components/ledger/ledger-request-detail.tsx` — current request-led evidence surface. It already renders the persisted governance markers directly (`Evidence retention`, `Evidence expires at`, `Metadata minimization`, `Suppressed metadata fields`, `Governance source`). Useful mainly to preserve compatibility and possibly add bounded copy if S02 chooses to explain that rows may age out due to persisted retention.
- `console/src/lib/admin-api.ts` — mirror of backend types. Currently includes `UsageLedgerRecord` governance fields, but its `TenantPolicy` top block appears stale in the first portion of the file read; verify before planning console work so types stay aligned.
- `tests/test_governance_api.py` — strongest backend/admin seam test file. Already proves policy-options classification, governed ledger rows, embeddings correlation, and absence of raw input/embedding payloads. Best home for retention cleanup and admin read-path proof.
- `tests/test_chat_completions.py` — proves chat ledger rows carry governed markers. Extend only if integrated proof needs chat-generated expired rows/cleanup.
- `tests/test_embeddings_api.py` — proves embeddings rows carry governed markers and request correlation. Extend only if you want cross-writer proof that both message types delete through the shared seam.
- `tests/support.py` — test harness runs Alembic migrations per temp DB and is the correct place to rely on migrated schema during store-level retention tests.
- `src/nebula/models/hosted_contract.py` / `tests/test_hosted_contract.py` — guardrail files proving hosted export remains metadata-only and excludes `raw_usage_ledger_rows`. Re-run when retention work is done to ensure no trust-boundary drift.

### Build Order

1. **Prove the store seam first** in `GovernanceStore`.
   - Add explicit cleanup behavior around `usage_ledger` using persisted `evidence_expires_at`.
   - Make it idempotent: repeated cleanup passes should safely delete zero already-removed rows.
   - Prefer a method that returns a small count/summary for tests and operational proof.

2. **Cover admin/read-path behavior next**.
   - Verify expired rows disappear from `list_usage_records()` / `GET /v1/admin/usage/ledger` after cleanup.
   - If a manual cleanup trigger is needed for bounded proof, expose it through existing admin seams rather than new subsystem surfaces.

3. **Only then adjust request-detail/read-surface compatibility if needed**.
   - The current console request-detail already renders the historical governance markers correctly for surviving rows.
   - Keep any UI change minimal and request-led; do not build a governance dashboard.

4. **Finish with integrated proof** across chat/embeddings and hosted-boundary checks.
   - One request is written with governance markers.
   - Cleanup executes after expiration.
   - The row is actually gone from the ledger read path.
   - Hosted contract tests still exclude raw ledger export.

### Verification Approach

Backend-first verification should be sufficient for this slice:

- `./.venv/bin/pytest tests/test_governance_api.py`
  - Add/extend tests for retention cleanup, deletion idempotence, and admin ledger absence after cleanup.
- `./.venv/bin/pytest tests/test_chat_completions.py -k ledger`
  - Reconfirm chat rows still persist governed markers before cleanup.
- `./.venv/bin/pytest tests/test_embeddings_api.py`
  - Reconfirm embeddings rows still persist governed markers and request correlation.
- `./.venv/bin/pytest tests/test_hosted_contract.py`
  - Reconfirm hosted metadata-only exclusion list still protects `raw_usage_ledger_rows`.

If a console touch is required:
- `npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx`

Observable behaviors to prove:
- A request persists `evidence_retention_window` + `evidence_expires_at` + historical governance markers on the row.
- Cleanup uses the persisted expiration marker, not current tenant policy inference.
- After cleanup, the expired row no longer appears in `/v1/admin/usage/ledger`.
- Re-running cleanup is safe and reports no harmful side effects.

## Constraints

- Keep governance local-authoritative and request-led; do not widen into hosted enforcement or compliance-platform workflows.
- Retention must mean **actual deletion**, not UI hiding or query-time filtering only.
- Use the existing ledger/store seam; do not duplicate governance logic in chat or embeddings writers.
- Preserve the hosted metadata-only boundary from `src/nebula/models/hosted_contract.py`; no raw ledger export additions.
- Per S01 forward intelligence: when verification uses pytest in this repo, prefer `./.venv/bin/pytest` if PATH pytest is missing.

## Common Pitfalls

- **Inferring expiration from current tenant policy** — cleanup should operate on persisted `evidence_expires_at` so historical truth survives later policy edits.
- **Implementing soft-delete or hidden-row behavior** — milestone context explicitly rejects visibility-only expiry; tests should prove rows are actually gone from `usage_ledger` reads.
- **Forking governance behavior by entry point** — chat and embeddings already share `GovernanceStore.record_usage()`; retention should be equally centralized.
- **Overbuilding operator surfaces** — request detail already has the right seam. Add only bounded explanatory copy if absolutely needed.

## Open Risks

- `console/src/lib/admin-api.ts` may have stale `TenantPolicy` typing near the top of the file despite later governance-aware ledger types; if planner schedules console work, verify the full file before editing to avoid type drift.
- There is not yet an obvious lifecycle trigger in `main.py` / `ServiceContainer` for periodic cleanup. If S02 needs runtime execution beyond explicit test/admin invocation, choose a bounded seam carefully so it remains observable and does not create background-process ambiguity.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| FastAPI | `wshobson/agents@fastapi-templates` | available via `npx skills add wshobson/agents@fastapi-templates` |
| Next.js | `wshobson/agents@nextjs-app-router-patterns` | available via `npx skills add wshobson/agents@nextjs-app-router-patterns` |
| SQLAlchemy/Alembic | `wispbit-ai/skills@sqlalchemy-alembic-expert-best-practices-code-review` | available via `npx skills add wispbit-ai/skills@sqlalchemy-alembic-expert-best-practices-code-review` |