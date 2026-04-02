# M006 integrated proof

This document is Nebula's canonical integrated walkthrough for the M006 calibrated-routing close-out proof.

It assembles the already-shipped M006 seams into one strict review path without redefining their contracts, replaying their detailed operator copy, or implying broader product scope. Keep these sources in their canonical roles:

- [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md) — stable calibrated/degraded route signals, additive score vocabulary, reason codes, and policy-outcome fragments
- [`docs/adoption-api-contract.md`](adoption-api-contract.md) — the only detailed public compatibility boundary for `POST /v1/chat/completions`
- `src/nebula/api/routes/chat.py` — the public response path that emits calibrated `X-Nebula-*` metadata plus `X-Request-ID`
- `GET /v1/admin/usage/ledger?request_id=...` in `src/nebula/api/routes/admin.py` — the persisted request-evidence seam for correlating one public response to one durable operator record
- `POST /v1/admin/tenants/{tenant_id}/policy/simulate` in `src/nebula/api/routes/admin.py` — the replay seam for checking calibrated, degraded, or rollout-disabled parity against recent tenant traffic
- `console/src/app/(console)/observability/page.tsx` and `console/src/components/ledger/ledger-request-detail.tsx` — the selected-request-first Observability and request-detail corroboration surfaces
- `tests/test_response_headers.py` and `tests/test_governance_api.py` — the focused executable proof seams for public headers, request-id-to-ledger correlation, replay parity, and bounded degraded or rollout-disabled behavior

Use this walkthrough when a reviewer needs one discoverable M006 story that proves calibrated live routing, request-id-to-ledger correlation, replay parity, bounded degraded or rollout-disabled semantics, and selected-request-first operator inspection all agree without widening Nebula beyond calibrated-routing scope.

## What this integrated proof establishes

The M006 proof is complete only when one reviewer can inspect the shipped calibrated-routing surfaces in order and reach the same narrow conclusion throughout:

1. route explanations reuse the stable calibrated vocabulary in [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md)
2. one real public `POST /v1/chat/completions` response exposes calibrated `X-Nebula-*` metadata and `X-Request-ID`
3. the same request is durably correlated through `GET /v1/admin/usage/ledger?request_id=...`
4. replay through `policy/simulate` stays aligned with those persisted runtime signals instead of inventing a second routing story
5. degraded replay and rollout-disabled/null-mode semantics stay bounded, explicit, and operator-readable
6. Observability keeps the selected persisted request as the primary inspection surface, with supporting context remaining subordinate
7. the assembled proof stays within calibrated-routing scope and does not turn into a new analytics, tuning, hosted-authority, or public-API story

If any step in this walkthrough starts implying new tuning authority, hidden optimization, new admin API families, or broader platform scope, the proof has drifted outside M006.

## Canonical proof order

Follow this sequence in order and keep each seam in its existing role.

### 1. Start with the route-decision vocabulary

Begin with [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md).

This document is the stable explanation seam for M006 because it defines the calibrated-versus-degraded vocabulary, additive score components, reason codes, route_mode semantics, and bounded policy-outcome fragments that public headers, usage-ledger rows, replay output, and operator surfaces must continue to reuse. Reviewers should confirm here that Nebula's calibrated-routing story stays interpretable:

- calibrated and degraded routing are named explicitly
- additive score components remain visible and audit-friendly
- override and policy-forced paths stay signal-free when calibrated scoring did not participate
- rollout-disabled or policy-gated paths remain explicit instead of being treated as missing data

The integrated proof starts here because later surfaces should point back to this vocabulary rather than inventing new explanation language.

### 2. Use one real public `POST /v1/chat/completions` request

Next inspect the public request path itself: `POST /v1/chat/completions`.

The complete request and response contract lives in [`docs/adoption-api-contract.md`](adoption-api-contract.md). This walkthrough depends on that contract instead of restating it. For M006 close-out, the key point is that one real public response should expose the calibrated-routing evidence directly on the public seam before any admin-only corroboration is used.

The immediate public evidence includes:

- `X-Request-ID`
- the calibrated `X-Nebula-*` headers
- `X-Nebula-Route-Score`
- `X-Nebula-Route-Mode` when calibrated scoring participated
- route-target, route-reason, provider, fallback, and policy-outcome headers that remain consistent with the stable vocabulary

If `X-Request-ID` is missing, if the public `X-Nebula-*` evidence is skipped, or if the calibrated headers contradict the route vocabulary, the integrated proof is incomplete before operator surfaces are even opened.

### 3. Correlate the same request in `GET /v1/admin/usage/ledger?request_id=...`

Use the `X-Request-ID` from the public response to inspect the persisted operator record in `GET /v1/admin/usage/ledger?request_id=...`.

This is the canonical durable proof seam because it shows that the same public request was recorded as operator evidence, not just observed transiently in a response. The aligned record should preserve the same routing story across persisted fields such as:

- `request_id`
- `final_route_target`
- `final_provider`
- `route_reason`
- `policy_outcome`
- `route_signals` when calibrated routing participated
- terminal status, cache, fallback, token, and timing metadata

This step matters because M006 does not prove calibrated routing with headers alone. It proves that the public request and the persisted operator evidence agree on the same request.

### 4. Use `POST /v1/admin/tenants/{tenant_id}/policy/simulate` to confirm replay parity

After the public request and usage-ledger row agree, inspect `POST /v1/admin/tenants/{tenant_id}/policy/simulate`.

This is the canonical replay seam for M006. The proof should show that replay stays grounded in recent ledger-backed traffic and can be compared directly against the persisted runtime evidence from the earlier steps. Reviewers should confirm that simulation preserves the bounded calibrated-routing story:

- baseline changed-request evidence points back to persisted runtime signals
- calibrated replay stays calibrated when replay-critical inputs are present
- degraded replay stays explicit when replay-critical calibrated inputs are incomplete
- rollout-disabled outcomes remain explicit null-mode or gated semantics rather than being folded into degraded routing
- approximation stays operator-readable and bounded instead of becoming a hidden optimization layer

The replay proof is only strong when it starts from a real runtime request plus the correlated persisted ledger row. Synthetic-only replay examples are useful for shape coverage, but they are not the close-out proof path.

### 5. Use Observability as selected-request-first corroboration

Next inspect `console/src/app/(console)/observability/page.tsx` together with `console/src/components/ledger/ledger-request-detail.tsx`.

Observability closes the operator proof path because it lets reviewers inspect the same persisted request inside the shipped operator surface. The page should preserve a strict hierarchy:

- the selected ledger row remains the authoritative request evidence
- request detail explains the persisted calibrated, degraded, rollout-disabled, or unscored state for that row
- tenant-scoped calibration, recommendation, cache, and dependency panels remain supporting context
- Observability does not replace the public `X-Request-ID` or `GET /v1/admin/usage/ledger?request_id=...` seams

This step is important because the integrated proof should make later drift obvious: if Observability starts reading like a broader analytics product, a new authority layer, or a replacement for the selected request evidence, the proof has widened beyond scope.

## How the canonical sources fit together

Use this map when deciding which source to open for detail.

| Need | Canonical source | Why it stays separate |
|---|---|---|
| Stable calibrated/degraded route vocabulary, additive score components, and policy-outcome fragments | [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md) | Prevents explanation drift across headers, ledger, replay, and UI surfaces |
| Detailed public `POST /v1/chat/completions` boundary | [`docs/adoption-api-contract.md`](adoption-api-contract.md) | Prevents this walkthrough from becoming a second public contract |
| Public response metadata emission | `src/nebula/api/routes/chat.py` | Keeps the concrete header boundary tied to the shipped route |
| Persisted request-id correlation | `GET /v1/admin/usage/ledger?request_id=...` in `src/nebula/api/routes/admin.py` | Keeps durable operator evidence anchored to the shipped admin route |
| Replay parity and bounded changed-request inspection | `POST /v1/admin/tenants/{tenant_id}/policy/simulate` in `src/nebula/api/routes/admin.py` | Keeps the simulation capability tied to the shipped admin seam |
| Selected-request-first operator inspection | `console/src/app/(console)/observability/page.tsx` and `console/src/components/ledger/ledger-request-detail.tsx` | Keeps request evidence primary and supporting context bounded |
| Executable proof for public headers, ledger correlation, and replay parity | `tests/test_response_headers.py` and `tests/test_governance_api.py` | Keeps the close-out story grounded in code-backed verification rather than prose snapshots |

## Minimal operator walkthrough

Use this concise path when you need the full M006 proof in one review sequence:

1. Start in [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md) and confirm the stable calibrated/degraded route vocabulary and additive score semantics.
2. Send one real public `POST /v1/chat/completions` request using the contract in [`docs/adoption-api-contract.md`](adoption-api-contract.md).
3. Record `X-Request-ID` and inspect the calibrated `X-Nebula-*` headers on that public response.
4. Query `GET /v1/admin/usage/ledger?request_id=...` for the same request id and confirm the persisted row matches the public routing evidence.
5. Inspect `POST /v1/admin/tenants/{tenant_id}/policy/simulate` and confirm replay changed-request fields stay aligned with the persisted runtime evidence, including calibrated, degraded, or rollout-disabled cases as applicable.
6. Open Observability and inspect the same selected request in request detail, confirming supporting panels remain subordinate to that persisted request evidence.
7. Use the focused executable seams in `tests/test_response_headers.py` and `tests/test_governance_api.py` as code-backed confirmation that the assembled runtime, replay, and operator story still holds in the shipped worktree.

That is Nebula's canonical integrated M006 proof path.

## What this walkthrough intentionally does not duplicate

This document does not duplicate the detailed request contract, operator copy, or replay implementation details it depends on.

It intentionally does not duplicate:

- the detailed route vocabulary already defined in [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md)
- the complete public `POST /v1/chat/completions` contract already defined in [`docs/adoption-api-contract.md`](adoption-api-contract.md)
- the full header implementation details already present in `src/nebula/api/routes/chat.py`
- the complete usage-ledger and `policy/simulate` route implementation details already present in `src/nebula/api/routes/admin.py`
- the full selected-request and supporting-panel UI behavior already shipped in `console/src/app/(console)/observability/page.tsx` and `console/src/components/ledger/ledger-request-detail.tsx`
- the full executable assertions already proven in `tests/test_response_headers.py` and `tests/test_governance_api.py`

If one of those details changes, update the canonical source rather than copying replacement detail here.

## Failure modes this integrated proof makes obvious

These failure modes are the review shortcuts that reveal calibrated-routing scope drift or broken proof ordering before a reviewer has to infer it from code.

The integrated proof has failed if any of these become true:

- route explanations no longer point back to the stable vocabulary in [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md)
- the public `POST /v1/chat/completions` request is no longer the first runtime proof step
- `X-Request-ID` or calibrated `X-Nebula-*` metadata stop being the first explainability surface on the public response
- `GET /v1/admin/usage/ledger?request_id=...` is omitted, replaced, or no longer aligns with the public request evidence
- replay through `policy/simulate` stops reading from recent ledger-backed evidence or stops preserving bounded calibrated, degraded, and rollout-disabled semantics
- degraded replay and rollout-disabled/null-mode behavior stop being distinguished clearly for operators
- Observability is described as more authoritative than the selected request evidence and persisted ledger correlation path
- the walkthrough starts implying a broader analytics surface, autonomous tuning, hidden weighting authority, or new hosted/public product scope not already shipped

## Related docs and code-backed seams

- [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md) — stable calibrated-routing explanation seam
- [`docs/adoption-api-contract.md`](adoption-api-contract.md) — canonical public chat contract
- `src/nebula/api/routes/chat.py` — public header emission seam for `POST /v1/chat/completions`
- `src/nebula/api/routes/admin.py` — usage-ledger and `policy/simulate` admin seams
- `console/src/app/(console)/observability/page.tsx` — selected-request-first Observability framing
- `console/src/components/ledger/ledger-request-detail.tsx` — request-detail inspection surface
- `tests/test_response_headers.py` — public calibrated-header proof seam
- `tests/test_governance_api.py` — request-id-to-ledger and replay-parity proof seam
