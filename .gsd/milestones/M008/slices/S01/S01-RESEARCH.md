# Slice Research — M008/S01

## Summary
- S01 directly owns **R056** and **R057**, and supports **R062** and **R064**. The codebase already has the exact policy/admin/ledger seams this slice needs, but today evidence governance is still mostly absent: `TenantPolicy` only carries advisory `prompt_capture_enabled` / `response_capture_enabled`, the ledger row has no historical governance markers, and there is no retention/minimization runtime behavior.
- The backend is the critical first seam. `src/nebula/models/governance.py`, `src/nebula/db/models.py`, `src/nebula/services/governance_store.py`, `src/nebula/api/routes/admin.py`, `src/nebula/services/chat_service.py`, and `src/nebula/api/routes/embeddings.py` define the full policy → persistence → readback loop. S01 can land typed policy fields and runtime-enforced persistence behavior without touching broader routing architecture.
- The console already has bounded UX patterns that fit M008 well. `console/src/components/policy/policy-form.tsx` renders runtime-enforced vs advisory groupings, `policy-advanced-section.tsx` is an explicit placeholder for deferred capture/governance work, and `ledger-request-detail.tsx` is already the authoritative request-evidence surface. That means S01 should add typed evidence-governance controls to the existing policy editor and API contract, not invent a new governance dashboard.
- Hosted metadata-only trust-boundary files are already strongly guarded: `src/nebula/models/hosted_contract.py`, `docs/hosted-default-export.schema.json`, and `tests/test_hosted_contract.py`. S01 should not widen them; the planner should treat them mainly as “must not drift” verification context rather than primary implementation targets.

## Recommendation
1. **Start in backend models + migrations first.** Add typed evidence-governance fields to Pydantic + SQLAlchemy + Alembic before any UI work. This is the highest-risk seam because it defines the stable contract for later slices and must support true runtime enforcement, not advisory metadata.
2. **Implement governed persistence in `GovernanceStore.record_usage` (or a helper just beneath it), not ad hoc in each route.** Both chat and embeddings already funnel through this store; centralizing minimization logic here keeps enforcement coherent and makes S01’s proof tractable.
3. **Persist request-level governance markers immediately in the ledger row shape, even if S02 will explain them in UI later.** The milestone context is explicit that historical truth must be row-level, not inferred from current policy. S01 should establish that schema now so later slices consume it.
4. **Expose the new policy fields through `/v1/admin/tenants/{tenant_id}/policy` and `/v1/admin/policy/options` and wire the policy form to them using the existing runtime-enforced/advisory grouping pattern.** This is straightforward once the backend contract exists.
5. **Keep hosted contract verification in tests as a guardrail, not a feature expansion.** That aligns with R064 and the existing hosted contract tests.

## Implementation Landscape

### Existing files and what they do
- `src/nebula/models/governance.py`
  - Canonical Pydantic contract for `TenantPolicy`, `UsageLedgerRecord`, admin policy options, and admin API payloads.
  - Today `TenantPolicy` has routing/cache/budget controls plus advisory `prompt_capture_enabled` and `response_capture_enabled` booleans.
  - `UsageLedgerRecord` currently contains request identity, routing/provider/tokens/cost/timestamp/policy outcome/route signals only.
  - Natural place to add typed evidence governance policy fields and new persisted governance marker fields.

- `src/nebula/db/models.py`
  - SQLAlchemy persistence layer for `tenant_policies` and `usage_ledger`.
  - `TenantPolicyModel` mirrors current routing/cache/budget fields plus advisory capture booleans.
  - `UsageLedgerModel` has no retention/minimization/governance columns yet.
  - S01 schema changes will likely land here first and require a new Alembic revision.

- `migrations/versions/*.py`
  - Existing migration style is additive and idempotent-by-inspection (`inspect(bind).get_columns(...)` before adding columns).
  - Relevant prior art:
    - `20260315_0001_governance_baseline.py` created `tenant_policies` and `usage_ledger`
    - `20260326_0006_route_signals.py` added `route_signals`
    - `20260328_0008_cache_policy_controls.py` added cache tuning policy columns
    - `20260401_0009_calibrated_routing_rollout.py` added `calibrated_routing_enabled`
  - S01 should follow the same additive migration pattern.

- `src/nebula/services/governance_store.py`
  - Current source of truth for policy persistence/readback and ledger writes.
  - `upsert_policy()` persists all `TenantPolicy` fields explicitly.
  - `record_usage()` writes ledger rows directly from `UsageLedgerRecord` with no evidence minimization/retention/governance transformation.
  - `list_usage_records()` and `_usage_from_model()` define readback shape.
  - Best backend seam for runtime-enforced metadata suppression and, if needed, future retention helpers.

- `src/nebula/services/chat_service.py`
  - Main completion path. All successful/error/cache/fallback request outcomes funnel through `_record_usage()` or direct `governance_store.record_usage(...)` for denials.
  - Currently persists full `UsageLedgerRecord` shape unconditionally.
  - Important constraint: S01 should not duplicate minimization rules across cache hit / completion / fallback / denial branches if store-level enforcement can handle it centrally.

- `src/nebula/api/routes/embeddings.py`
  - Separate request-evidence writer for embeddings; writes `UsageLedgerRecord` directly through `_record_usage()` helper.
  - Important because S01’s evidence governance must cover this path too, or the milestone proof will be inconsistent.

- `src/nebula/api/routes/admin.py`
  - Exposes `GET/PUT /tenants/{tenant_id}/policy`, `GET /policy/options`, and `GET /usage/ledger`.
  - `get_policy_options()` currently explicitly labels `prompt_capture_enabled` and `response_capture_enabled` as advisory fields, while routing/cache/budget fields are runtime-enforced or soft-signal.
  - S01 will need to extend this field taxonomy for evidence governance so the UI can truthfully distinguish enforced vs advisory.

- `console/src/lib/admin-api.ts`
  - TypeScript mirror of `TenantPolicy`, `UsageLedgerRecord`, and policy options.
  - Any backend contract change must be reflected here for the policy page and ledger request detail to compile.

- `console/src/components/policy/policy-form.tsx`
  - Existing policy editor with clear sectioning: runtime-enforced controls, soft-budget advisory, and separate preview-before-save flow.
  - `PolicyFormState` currently only includes routing/cache/budget values; `toPolicyPayload()` preserves the untouched `initialPolicy` fields via spread.
  - Strong fit for adding evidence governance controls in the runtime-enforced area, likely as a bounded new sub-section rather than a new page.

- `console/src/components/policy/policy-advanced-section.tsx`
  - Simple placeholder: “Deferred capture settings are not editable.”
  - This is the cleanest UI seam for replacing/expanding the existing deferred-governance copy without implying payload capture scope creep.

- `console/src/components/ledger/ledger-request-detail.tsx`
  - Current selected-row evidence surface. Already emphasizes “This persisted ledger record is the authoritative evidence row for this request ID.”
  - Renders row fields plus optional calibration/budget/routing explanations.
  - S01 probably should not over-expand this yet, but it must preserve compatibility with future governance-marker display. This file is the downstream consumer for persisted markers.

- `src/nebula/models/hosted_contract.py`, `docs/hosted-default-export.schema.json`, `tests/test_hosted_contract.py`
  - Canonical hosted metadata-only allowlist and drift tests.
  - No evidence-governance fields exist here; that is correct for now. S01 should preserve this boundary and may only need tests/docs proving no leakage.

### Natural seams for task decomposition
1. **Contract + schema seam**
   - `src/nebula/models/governance.py`
   - `src/nebula/db/models.py`
   - `migrations/versions/<new>.py`
   - Possibly tests that assert exact policy/options/ledger shapes
   - This is the first unblocker.

2. **Runtime enforcement seam**
   - `src/nebula/services/governance_store.py`
   - `src/nebula/services/chat_service.py`
   - `src/nebula/api/routes/embeddings.py`
   - Backend tests in `tests/test_governance_api.py`, `tests/test_chat_completions.py`, `tests/test_embeddings_api.py`
   - Goal: new policy values change what gets persisted on each row.

3. **Admin contract / options seam**
   - `src/nebula/api/routes/admin.py`
   - `console/src/lib/admin-api.ts`
   - Policy page tests/components
   - Goal: operator-facing typed policy contract is truthfully exposed as runtime-enforced.

4. **Console policy UI seam**
   - `console/src/app/(console)/policy/page.tsx`
   - `console/src/components/policy/policy-form.tsx`
   - `console/src/components/policy/policy-advanced-section.tsx`
   - `console/src/components/policy/policy-form.test.tsx`
   - `console/src/components/policy/policy-page.test.tsx`
   - Goal: bounded controls on existing page, preserving compare-before-save behavior.

5. **Downstream request-detail readiness seam**
   - `console/src/components/ledger/ledger-request-detail.tsx`
   - `console/src/components/ledger/ledger-request-detail.test.tsx`
   - S01 may only need to keep type compatibility or lay groundwork; richer explanation likely belongs more to S02/S04.

### What is missing today
- No typed evidence retention field on tenant policy.
- No typed metadata minimization field on tenant policy.
- No runtime policy options metadata that classifies evidence governance controls as enforced.
- No ledger-row fields for governance markers or deletion/minimization status.
- No store-level suppression/minimization behavior before persistence.
- No retention execution path or cleanup helper in `GovernanceStore` yet.
- No tests for evidence governance policy validation, persisted markers, or retention policy fields.

## Constraints and Risks
- **Historical truth constraint:** The milestone context explicitly rejects inferring governance from current tenant policy. If S01 adds policy fields but not row-level markers, it will create rework for S02 and weaken R058/R062 support.
- **Single-source enforcement constraint:** Chat and embeddings both write usage evidence. If minimization is implemented only in `ChatService`, embeddings will drift immediately. `GovernanceStore.record_usage()` is the safer enforcement seam.
- **Schema drift risk across Python + TS:** `TenantPolicy`, `UsageLedgerRecord`, and `PolicyOptionsResponse` are mirrored in `console/src/lib/admin-api.ts`; forgetting one side will break UI/tests.
- **Migration compatibility risk:** The test harness always runs `alembic upgrade head` via `tests/support.py`. Any new migration must be idempotent and compatible with fresh SQLite databases.
- **Scope creep risk:** Existing placeholder text and advisory capture booleans could tempt payload-capture UI. The milestone context and hosted contract both say raw prompts/responses remain out of scope.
- **Hosted-boundary drift risk:** If evidence governance fields are naively exported or described as hosted-authoritative, S01 would violate R061/R064. Existing `test_hosted_contract.py` is the regression tripwire.

## Verification

### Backend verification likely needed
- `pytest tests/test_governance_api.py`
  - Extend with policy CRUD assertions for new evidence governance fields.
  - Add `/v1/admin/policy/options` assertions showing new fields are runtime-enforced, not advisory.
  - Add ledger assertions proving persisted rows carry governed/minimized shape and governance markers.

- `pytest tests/test_chat_completions.py -k ledger`
  - Verify chat-completion write path respects minimization and marker persistence.

- `pytest tests/test_embeddings_api.py`
  - Verify embeddings evidence path also respects the same governance rules.

- `pytest tests/test_hosted_contract.py`
  - Guard against hosted metadata-only boundary drift.

- Possibly a new targeted test module for `GovernanceStore` or policy validation if the logic gets too dense for API tests.

### Frontend verification likely needed
- `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx`
  - Policy form/page for new controls and copy.
  - Request detail only if S01 changes the row type or adds minimal governance placeholders.

### Migration / integration verification
- `make test` after targeted runs if the slice changes shared models used broadly.
- Fresh test-app startup already exercises migrations via `tests/support.py`; no separate custom migration harness seems necessary unless a retention job/service is introduced.

## Skill Discovery
- Installed skills already directly relevant:
  - `react-best-practices` — useful for Next.js/React policy UI updates.
  - `best-practices` — useful for bounded, security-sensitive governance changes.
- Promising external skills not installed:
  - FastAPI: `npx skills add wshobson/agents@fastapi-templates` (highest install count, directly relevant to admin API contract work)
  - Next.js: `npx skills add wshobson/agents@nextjs-app-router-patterns` (highest install count, directly relevant to console page/component work)
  - SQLAlchemy/Alembic: `npx skills add wispbit-ai/skills@sqlalchemy-alembic-expert-best-practices-code-review` (most relevant to migration + ORM evolution, though lower install count)
- I did not install any of these.

## Sources
- Codebase only; no external library docs were needed because this slice uses established project patterns (FastAPI + Pydantic + SQLAlchemy + Next.js/React) already present in-repo.

## Planner Notes
- Build order should be **schema/contracts → persistence enforcement → admin options/API → console policy UI → verification**.
- The riskiest ambiguity the executor must resolve early is the exact typed policy shape for “retention” and “metadata minimization.” Once that is chosen, the rest of the file touch list is narrow and obvious.
- Prefer one central “governed ledger row” transformation seam in `GovernanceStore` over sprinkling conditional field suppression across route handlers.
- Keep `ledger-request-detail.tsx` changes minimal in S01 unless the backend contract forces type updates; request-detail explanation depth is a later-slice concern, but row schema compatibility should be designed now.