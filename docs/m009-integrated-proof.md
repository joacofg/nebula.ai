# M009 integrated proof

This document is Nebula's canonical integrated walkthrough for the M009 close-out proof.

It assembles the already-shipped M009 seams into one strict pointer-first review path without redefining their contracts, replaying detailed operator copy, or implying broader product scope. Keep these sources in their canonical roles:

- [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md) — stable route vocabulary, shared outcome-evidence terms, additive score factors, and degraded-versus-calibrated explanation seams
- [`docs/adoption-api-contract.md`](adoption-api-contract.md) — the only detailed public compatibility boundary for `POST /v1/chat/completions`
- `src/nebula/api/routes/chat.py` — the public response path that emits `X-Request-ID` plus the shipped `X-Nebula-*` metadata
- `GET /v1/admin/usage/ledger?request_id=...` in `src/nebula/api/routes/admin.py` — the persisted request-evidence seam for correlating one public response to one durable operator row
- `POST /v1/admin/tenants/{tenant_id}/policy/simulate` in `src/nebula/api/routes/admin.py` — the replay seam for checking parity against the persisted request evidence instead of inventing a second routing story
- `console/src/app/(console)/observability/page.tsx` and `console/src/components/ledger/ledger-request-detail.tsx` — the selected-request-first Observability and request-detail corroboration surfaces
- focused pytest and Vitest seams covering public headers, usage-ledger correlation, replay parity, and request-first operator inspection — the executable anti-drift proof that these shipped seams still agree

Use this walkthrough when a reviewer needs one discoverable M009 story that proves a single public request, its persisted evidence, replay parity, and request-first operator inspection still agree for both a happy path and a degraded path without widening Nebula beyond the existing runtime, admin, and console surfaces.

## What this integrated proof establishes

The M009 proof is complete only when one reviewer can inspect the shipped seams in order and reach the same narrow conclusion throughout:

1. route explanations reuse the stable vocabulary in [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md) instead of redefining outcome-grounded fields inline
2. one real public `POST /v1/chat/completions` response exposes `X-Request-ID` and the shipped `X-Nebula-*` routing evidence first
3. the same request is durably correlated through `GET /v1/admin/usage/ledger?request_id=...`
4. replay through `POST /v1/admin/tenants/{tenant_id}/policy/simulate` stays aligned with that persisted request evidence for both a happy path and a degraded path
5. Observability keeps selected-request-first inspection and request detail as the canonical operator corroboration surfaces
6. the assembled proof stays within the shipped runtime, admin, and console seams rather than turning into a new analytics, hosted-authority, or dashboard story

If any step in this walkthrough starts inventing a second route vocabulary, bypassing the persisted request row, or treating tenant-wide context as more authoritative than the selected request, the proof has drifted outside M009.

## Canonical proof order

Follow this sequence in order and keep each seam in its existing role.

### 1. Start with the route-decision vocabulary

Begin with [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md).

This document is the stable explanation seam for M009 because it already defines the route terms, outcome-grounded evidence names, additive score factors, and degraded-versus-calibrated semantics that later seams must continue to reuse. Reviewers should confirm here that:

- the route story remains interpretable through one shared vocabulary
- `outcome_bonus`, `evidence_penalty`, and `outcome_evidence` are discoverable here instead of being redefined later in a walkthrough or UI surface
- degraded behavior remains explicit rather than being treated as missing or mysterious data
- operator-facing explanation terms stay shared across runtime headers, persisted ledger rows, replay output, and request detail

The integrated proof starts here because later surfaces should point back to this vocabulary rather than inventing replacement language.

### 2. Use one real public `POST /v1/chat/completions` request

Next inspect the public request path itself: `POST /v1/chat/completions`.

The complete request and response contract lives in [`docs/adoption-api-contract.md`](adoption-api-contract.md). This walkthrough depends on that contract instead of restating it. For M009 close-out, the key point is that one real public response should expose the first runtime evidence directly on the public seam before any admin-only corroboration is used.

The immediate public evidence includes:

- `X-Request-ID`
- the shipped `X-Nebula-*` headers
- route-target, route-reason, provider, fallback, and policy-outcome metadata that remain consistent with the route vocabulary
- any response metadata needed to make the later ledger row and replay inspection legible

If `X-Request-ID` is missing, if the public `X-Nebula-*` evidence is skipped, or if the public route explanation contradicts the shared vocabulary, the integrated proof is incomplete before operator surfaces are even opened.

### 3. Correlate the same request in `GET /v1/admin/usage/ledger?request_id=...`

Use the `X-Request-ID` from the public response to inspect the persisted operator record in `GET /v1/admin/usage/ledger?request_id=...`.

This is the canonical durable proof seam because it shows that the same public request was recorded as operator evidence, not just observed transiently in a response. The aligned row should preserve the same request-first story across persisted fields such as:

- `request_id`
- final route, provider, route reason, and policy outcome
- persisted route evidence needed for replay parity and request-detail inspection
- any bounded outcome-evidence fields already defined in the shared vocabulary

This step matters because M009 does not prove request-first explainability with headers alone. It proves that the public request and the durable operator evidence still agree on the same request.

### 4. Use `POST /v1/admin/tenants/{tenant_id}/policy/simulate` to confirm replay parity

After the public request and usage-ledger row agree, inspect `POST /v1/admin/tenants/{tenant_id}/policy/simulate`.

This is the canonical replay seam for M009. The proof should show that replay stays grounded in persisted request evidence and can be compared directly against the earlier runtime and ledger steps. Reviewers should confirm that:

- the replay explanation points back to persisted request evidence instead of inventing a second route vocabulary
- a happy path replay stays aligned with the persisted request story when replay-critical evidence is present
- a degraded path replay stays explicit and operator-readable when replay-critical evidence is incomplete or reconstructed
- replay parity remains narrow: it corroborates the selected request instead of becoming a broader policy studio or analytics layer

The replay proof is only strong when it starts from a real runtime request plus the correlated persisted ledger row. Synthetic-only examples may help with shape coverage, but they are not the M009 close-out proof path.

### 5. Use Observability as selected-request-first corroboration

Next inspect `console/src/app/(console)/observability/page.tsx` together with `console/src/components/ledger/ledger-request-detail.tsx`.

Observability closes the operator proof path because it lets reviewers inspect the same persisted request inside the shipped operator surface. The page should preserve a strict hierarchy:

- the selected request remains the authoritative evidence seam
- request detail explains the persisted route, provider, fallback, policy outcome, and bounded outcome-evidence story for that row
- supporting tenant-scoped context remains subordinate to the same request investigation
- selected-request-first inspection stays canonical for both the happy path and the degraded path

This step is important because the integrated proof should make later drift obvious: if Observability starts reading like a broader dashboard or an authority layer that replaces the selected request evidence, the proof has widened beyond scope.

### 6. Finish with the focused executable proof seams

Finally inspect the focused backend and console verification seams that exercise the assembled story.

These seams are the executable anti-drift proof for M009 because they keep the pointer-first walkthrough grounded in shipped behavior rather than prose snapshots. Reviewers should confirm that the code-backed checks still cover:

- one public `POST /v1/chat/completions` response exposing the expected request-id and route evidence
- durable `GET /v1/admin/usage/ledger?request_id=...` correlation
- `POST /v1/admin/tenants/{tenant_id}/policy/simulate` parity against the persisted request evidence
- request-first operator inspection and request-detail corroboration
- both a happy path and a degraded path remaining explicit and bounded

## How the canonical sources fit together

Use this map when deciding which source to open for detail.

| Need | Canonical source | Why it stays separate |
|---|---|---|
| Stable route vocabulary and shared outcome-evidence terms | [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md) | Prevents headers, ledger rows, replay output, and request detail from inventing different explanation language |
| Detailed public `POST /v1/chat/completions` boundary | [`docs/adoption-api-contract.md`](adoption-api-contract.md) | Prevents this walkthrough from becoming a second public contract |
| Public request-id and routing metadata emission | `src/nebula/api/routes/chat.py` | Keeps the concrete header boundary tied to the shipped route |
| Durable request-id correlation | `GET /v1/admin/usage/ledger?request_id=...` in `src/nebula/api/routes/admin.py` | Keeps persisted operator evidence anchored to the shipped admin route |
| Replay parity for the selected request | `POST /v1/admin/tenants/{tenant_id}/policy/simulate` in `src/nebula/api/routes/admin.py` | Keeps simulation tied to the shipped replay seam rather than a second analysis product |
| selected-request-first operator inspection | `console/src/app/(console)/observability/page.tsx` and `console/src/components/ledger/ledger-request-detail.tsx` | Keeps the selected request primary and supporting context bounded |
| Executable anti-drift proof | focused pytest and Vitest seams covering headers, ledger correlation, replay parity, and request detail | Keeps the close-out story grounded in code-backed verification rather than prose-only interpretation |

## Minimal operator walkthrough

Use this concise path when you need the full M009 proof in one review sequence:

1. Start in [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md) and confirm the stable route vocabulary plus shared outcome-evidence terms.
2. Send one real public `POST /v1/chat/completions` request using the contract in [`docs/adoption-api-contract.md`](adoption-api-contract.md).
3. Record `X-Request-ID` and inspect the shipped `X-Nebula-*` headers on that public response.
4. Query `GET /v1/admin/usage/ledger?request_id=...` for the same request id and confirm the persisted row matches the public routing evidence.
5. Inspect `POST /v1/admin/tenants/{tenant_id}/policy/simulate` and confirm replay stays aligned with the persisted request evidence for both a happy path and a degraded path.
6. Open Observability and inspect the same selected request in request detail, confirming selected-request-first inspection remains primary and supporting context remains subordinate.
7. Use the focused executable seams as code-backed confirmation that the assembled runtime, persistence, replay, and operator story still holds in the shipped worktree.

That is Nebula's canonical integrated M009 proof path.

## What this walkthrough intentionally does not duplicate

This document does not duplicate the detailed request contract, the full route vocabulary, the detailed replay implementation, or the full operator copy it depends on.

It intentionally does not duplicate:

- the detailed route vocabulary already defined in [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md)
- the complete public `POST /v1/chat/completions` contract already defined in [`docs/adoption-api-contract.md`](adoption-api-contract.md)
- the full header implementation details already present in `src/nebula/api/routes/chat.py`
- the complete usage-ledger and `policy/simulate` route implementation details already present in `src/nebula/api/routes/admin.py`
- the full selected-request and request-detail UI behavior already shipped in `console/src/app/(console)/observability/page.tsx` and `console/src/components/ledger/ledger-request-detail.tsx`
- the full executable assertions already proven in the focused backend and console verification seams

If one of those details changes, update the canonical source rather than copying replacement detail here.

## Failure modes this integrated proof makes obvious

These failure modes are the review shortcuts that reveal M009 drift before a reviewer has to infer it from scattered code, tests, and operator surfaces.

The integrated proof has failed if any of these become true:

- route explanations no longer point back to the stable vocabulary in [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md)
- the public `POST /v1/chat/completions` request is no longer the first runtime proof step
- `X-Request-ID` or the shipped `X-Nebula-*` metadata stop being the first explainability surface on the public response
- `GET /v1/admin/usage/ledger?request_id=...` is omitted, replaced, or no longer aligns with the public request evidence
- `POST /v1/admin/tenants/{tenant_id}/policy/simulate` stops grounding replay in persisted request evidence or stops keeping the happy path and degraded path explicit
- Observability stops treating selected-request-first inspection and request detail as the canonical operator corroboration surfaces
- the walkthrough starts implying a broader analytics surface, hosted-authority layer, dashboard concept, or new API family not already shipped

## Related docs and code-backed seams

- [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md) — stable route vocabulary and outcome-evidence terms
- [`docs/adoption-api-contract.md`](adoption-api-contract.md) — canonical public chat contract
- `src/nebula/api/routes/chat.py` — public header emission seam for `POST /v1/chat/completions`
- `src/nebula/api/routes/admin.py` — usage-ledger and `policy/simulate` admin seams
- `console/src/app/(console)/observability/page.tsx` — selected-request-first Observability framing
- `console/src/components/ledger/ledger-request-detail.tsx` — request-detail inspection surface
- focused pytest and Vitest seams for public headers, usage-ledger correlation, replay parity, and request-first operator inspection
