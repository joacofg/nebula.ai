---
id: T02
parent: S01
milestone: M008
key_files:
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
key_decisions:
  - Kept evidence-governance controls inside the existing runtime-enforced policy section so operators see retention/minimization as live write-time behavior rather than deferred capture settings.
  - Generated fallback request IDs inside the embeddings writer to preserve response-header to ledger correlation even when request middleware state is absent.
duration: 
verification_result: mixed
completed_at: 2026-04-12T00:18:42.741Z
blocker_discovered: false
---

# T02: Wired governed evidence retention/minimization through chat, embeddings, and console policy/ledger surfaces with end-to-end coverage.

**Wired governed evidence retention/minimization through chat, embeddings, and console policy/ledger surfaces with end-to-end coverage.**

## What Happened

I verified the existing S01 backend contract from T01, then completed the remaining live wiring and operator-facing propagation for the governed evidence fields. On the backend, chat already recorded usage through GovernanceStore, so I added focused coverage proving tenant policy changes drive governed chat ledger markers. In the embeddings route I fixed the request writer so ledger rows always receive a stable generated request_id when middleware state is absent, keeping admin correlation truthful for embeddings as well as chat. I then extended the console admin client types to include evidence_retention_window, metadata_minimization_level, message_type, evidence_expires_at, metadata_fields_suppressed, and governance_source so the UI matched the backend contract instead of silently truncating the row shape. In the policy editor, I added bounded runtime-enforced controls for evidence retention window and metadata minimization level, plus explanatory copy that frames them as write-time enforcement rather than advisory capture settings. I also updated the deferred advanced section copy so prompt/response capture remains clearly advisory and out of scope for this phase. In ledger request detail, I kept the existing routing/budget/calibration sections but added the governed row markers directly to the detail grid so operators can see message type, retention window, expiration, minimization level, suppressed metadata fields, and governance source without manual JSON inspection. Finally, I expanded the targeted backend and Vitest suites so the S01 demo path is explicit: operator-configured policy reaches the live contract, chat and embeddings rows persist governed markers/minimized metadata, and the console truthfully exposes the runtime-enforced controls and rendered ledger fields. During execution I had to correct two local defects uncovered by verification: a stray indentation error at the end of src/nebula/api/routes/embeddings.py and a swallowed test boundary in tests/test_chat_completions.py after inserting the new ledger test. Both were fixed before final verification.

## Verification

Ran the exact task verification command from the task plan after completing the wiring: `./.venv/bin/pytest tests/test_chat_completions.py -k ledger && ./.venv/bin/pytest tests/test_embeddings_api.py && npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx`. Final result: the chat ledger governance test passed, all embeddings API tests passed including governed ledger persistence, and all 31 targeted console Vitest assertions passed for the policy form, policy page, and ledger request detail surfaces.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `./.venv/bin/pytest tests/test_chat_completions.py -k ledger && ./.venv/bin/pytest tests/test_embeddings_api.py && npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx` | 2 | ❌ fail | 2900ms |
| 2 | `./.venv/bin/pytest tests/test_chat_completions.py -k ledger && ./.venv/bin/pytest tests/test_embeddings_api.py && npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx` | 0 | ✅ pass | 3700ms |

## Deviations

The planner framed chat/embeddings writer changes as if both backends still needed full contract threading, but the chat path and most governance store behavior were already present from prior work. I therefore focused execution on filling the remaining live gaps: embeddings request-id correlation, console type/UI propagation, and targeted end-to-end assertions rather than broad backend rewrites.

## Known Issues

None.

## Files Created/Modified

- `src/nebula/api/routes/embeddings.py`
- `console/src/lib/admin-api.ts`
- `console/src/components/policy/policy-form.tsx`
- `console/src/components/policy/policy-advanced-section.tsx`
- `console/src/components/ledger/ledger-request-detail.tsx`
- `tests/test_chat_completions.py`
- `tests/test_embeddings_api.py`
- `console/src/components/policy/policy-form.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`
