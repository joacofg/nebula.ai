---
estimated_steps: 1
estimated_files: 11
skills_used: []
---

# T02: Wire chat, embeddings, and console policy surfaces to the governed evidence contract

Finish the slice by threading the typed governance fields through the live request writers and operator-facing policy boundary. Update chat and embeddings usage recording to populate the new row markers through the centralized store contract, mirror the backend type changes in the console admin client, and add bounded policy-form/policy-page UI controls plus copy that present evidence governance as runtime-enforced tenant controls rather than deferred advisory capture settings. Keep request-detail changes minimal but sufficient to stay type-compatible with the new ledger row shape and preserve space for later slices to explain those markers. Add backend and Vitest coverage proving the full S01 demo path: operator-configured policy reaches backend contracts, chat and embeddings ledger rows persist governed markers/minimized metadata, and the operator policy surface exposes the controls truthfully.

## Inputs

- `src/nebula/services/chat_service.py`
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
- `src/nebula/models/governance.py`
- `src/nebula/services/governance_store.py`
- `src/nebula/api/routes/admin.py`

## Expected Output

- `src/nebula/services/chat_service.py`
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

## Verification

pytest tests/test_chat_completions.py -k ledger && pytest tests/test_embeddings_api.py && npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx

## Observability Impact

Touches runtime evidence writers and the operator inspection surface. Failures should be diagnosable via response/ledger correlation in chat+embeddings tests and via UI tests asserting runtime-enforced copy and governed-field rendering, not by manual DOM inspection.
