---
id: S01
parent: M008
milestone: M008
provides:
  - Typed tenant-policy fields for evidence retention and metadata minimization.
  - A shared governed persistence seam for chat and embeddings usage writes.
  - Per-row governance markers that later slices can use for historical explanation and retention enforcement.
  - Operator-visible policy and request-detail surfaces already aligned to the new governed evidence contract.
requires:
  []
affects:
  - S02
  - S03
  - S04
  - S05
key_files:
  - src/nebula/services/governance_store.py
  - src/nebula/services/chat_service.py
  - src/nebula/api/routes/embeddings.py
  - tests/test_governance_api.py
  - tests/test_chat_completions.py
  - tests/test_embeddings_api.py
  - console/src/lib/admin-api.ts
  - console/src/components/policy/policy-form.tsx
  - console/src/components/policy/policy-advanced-section.tsx
  - console/src/components/ledger/ledger-request-detail.tsx
key_decisions:
  - Preserved evidence governance as typed runtime-enforced tenant policy fields plus per-row usage-ledger markers on the existing persistence seam rather than introducing raw payload capture or a separate governance subsystem.
  - Kept evidence-governance controls in the existing runtime-enforced policy surface so operators see retention/minimization as live write-time behavior, while prompt/response capture remains explicitly advisory and out of scope.
  - Generated fallback request IDs for embeddings usage recording so request-to-ledger correlation stays truthful even when middleware state is absent.
  - Preserved structured denied policy_outcome values in usage-ledger rows so operator inspection retains richer runtime context than the public error detail alone.
patterns_established:
  - Centralize evidence-governance enforcement in `GovernanceStore.record_usage()` so chat and embeddings cannot drift on retention/minimization behavior.
  - Persist request-time governance markers on each usage-ledger row instead of inferring historical policy from current tenant configuration.
  - Keep new governance controls inside existing policy and request-detail seams; expand explanation depth later without creating a separate governance dashboard.
  - When close-out verification fails because `pytest` is missing from PATH, rerun the required suites with `./.venv/bin/pytest` before treating the failure as product breakage.
observability_surfaces:
  - `/v1/admin/policy/options` now classifies evidence retention and metadata minimization as runtime-enforced controls rather than advisory settings.
  - `/v1/admin/usage/ledger` rows carry governance markers including message type, evidence expiration, minimization level, suppressed metadata fields, and governance source.
  - Console policy form and policy page expose the governed evidence controls and explain them as live write-time behavior.
  - Console request-detail renders the governed ledger fields directly so operators can inspect the effective evidence boundary for a persisted row.
drill_down_paths:
  - .gsd/milestones/M008/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M008/slices/S01/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-04-12T00:22:35.881Z
blocker_discovered: false
---

# S01: Typed evidence governance policy

**Established a typed, runtime-enforced evidence-governance contract across tenant policy, governed ledger persistence, and operator policy/request-detail surfaces without widening Nebula into payload capture or hosted-authority drift.**

## What Happened

S01 closed the first governance seam for M008 by turning evidence retention and metadata minimization into typed, runtime-enforced tenant policy rather than advisory settings. The assembled work now carries explicit `evidence_retention_window` and `metadata_minimization_level` fields through the backend governance contract, applies those controls centrally in `GovernanceStore.record_usage()` for both chat and embeddings writes, and persists request-time governance markers on usage-ledger rows so later slices can explain historical evidence truthfully. During close-out verification I confirmed the backend contract, admin policy/options classification, and hosted-boundary behavior through the targeted Python suites, and re-ran the console Vitest coverage to confirm operators can edit the new controls and inspect the resulting governed row fields. The slice also tightened local defects uncovered by verification: a blocking stray typo in `chat_service.py`, UTC normalization in governance-store calibration staleness handling, a malformed embeddings route boundary, and stale tests that no longer matched the intended structured denial and governance contract. The resulting slice establishes one bounded pattern for downstream work: use the existing tenant-policy and request-ledger boundaries, enforce governance at write time, persist historically truthful row markers, and keep raw prompt/response capture out of scope.

## Verification

Slice-level verification passed exactly against the planned checks after rerunning Python suites from the project virtualenv: `./.venv/bin/pytest tests/test_governance_api.py tests/test_service_flows.py tests/test_hosted_contract.py` (59 passed), `./.venv/bin/pytest tests/test_chat_completions.py -k ledger && ./.venv/bin/pytest tests/test_embeddings_api.py` (1 chat ledger test passed, 5 embeddings tests passed), and `npm --prefix console run test -- --run src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx` (31 Vitest assertions passed). These checks verified the runtime-enforced policy/options contract, governed chat and embeddings ledger persistence, request-detail/operator policy rendering, and the unchanged hosted metadata-only boundary.

## Requirements Advanced

- R056 — Implemented and verified explicit tenant policy control of evidence retention windows plus persisted expiration markers on usage-ledger rows.
- R057 — Implemented and verified explicit tenant policy control of metadata minimization with governed suppression of non-essential metadata while keeping raw payload capture out of scope.
- R058 — Established persisted governance markers on each ledger row as the historical truth source that later slices can explain more fully.
- R061 — Preserved the hosted metadata-only trust boundary while making local evidence governance visibly runtime-enforced and bounded.
- R062 — Advanced the end-to-end governance chain by closing the first leg: tenant policy to runtime persistence behavior to operator inspection surfaces.
- R064 — Kept M008 bounded to policy/request/evidence governance by reusing existing policy and request-detail seams instead of introducing compliance-platform or hosted-authority expansion.

## Requirements Validated

- R056 — Passing targeted backend verification with ./.venv/bin/pytest tests/test_governance_api.py tests/test_service_flows.py tests/test_hosted_contract.py plus chat/embeddings ledger tests proved explicit tenant retention policy fields and persisted evidence expiration markers.
- R057 — Passing backend and console verification proved metadata minimization is explicitly tenant-governed, enforced at write time, and rendered through existing operator surfaces without raw prompt/response capture.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

Most planned S01 feature surfaces were already present in the workspace before close-out, so the slice finish focused on verification-driven hardening and assembled proof rather than greenfield implementation. Verification uncovered and resolved local defects in chat-service importability, governance-store timestamp normalization, embeddings route structure, and stale test expectations.

## Known Limitations

S01 does not execute retention-driven deletion yet. It persists evidence expiration/minimization markers and enforces the write-time policy boundary, but real deletion remains deferred to S03. Request-detail compatibility was intentionally kept minimal; richer explanation of historical governance markers remains for later slices.

## Follow-ups

- S02 should build directly on the persisted row markers and make historical governance truth central to request evidence inspection, not re-derive policy from current tenant state.
- S03 must execute actual evidence deletion using the persisted expiration markers introduced here; S01 only establishes retention metadata and write-time enforcement.
- S04 should continue the bounded operator-surface approach by explaining effective evidence boundaries using existing policy and request-detail surfaces instead of adding a new governance dashboard.

## Files Created/Modified

- `src/nebula/services/governance_store.py` — Central governed persistence seam now normalizes calibration evidence timestamps and enforces typed evidence-governance markers on ledger writes.
- `src/nebula/services/chat_service.py` — Removed blocking module-scope typo discovered during verification so governance suites could collect and run.
- `src/nebula/api/routes/embeddings.py` — Embeddings writer now preserves request-to-ledger correlation through fallback request ID generation and governed usage recording.
- `tests/test_governance_api.py` — Governance API tests now assert typed retention/minimization policy behavior, runtime-enforced options classification, and structured denied policy outcomes.
- `tests/test_chat_completions.py` — Chat ledger coverage now proves governed retention/minimization markers persist on request evidence.
- `tests/test_embeddings_api.py` — Embeddings API coverage now proves governed ledger persistence and request correlation under the shared seam.
- `console/src/lib/admin-api.ts` — Console admin client types mirror the governed evidence policy and ledger row contract.
- `console/src/components/policy/policy-form.tsx` — Policy editor exposes runtime-enforced evidence retention and metadata minimization controls with bounded copy.
- `console/src/components/policy/policy-advanced-section.tsx` — Advanced policy copy now keeps prompt/response capture explicitly advisory and out of scope for M008/S01.
- `console/src/components/ledger/ledger-request-detail.tsx` — Request detail renders governed row markers so operators can inspect retention, minimization, suppression, and governance source without JSON digging.
