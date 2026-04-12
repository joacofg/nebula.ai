# M008 integrated governance proof

This document is Nebula's canonical integrated walkthrough for the M008 governance proof.

It assembles the already-shipped M008 seams into one strict review path without redefining their contracts, replaying their detailed operator copy, or implying broader product scope. Keep these sources in their canonical roles:

- `GET /v1/admin/policy/options` in `src/nebula/api/routes/admin.py` — the runtime-enforced policy/options seam that keeps evidence retention and metadata minimization fields explicit without inventing a second governance model
- `console/src/components/policy/policy-form.tsx` — the policy-side explanation seam for the effective evidence boundary and retention/minimization consequences
- `GET /v1/admin/usage/ledger?request_id=...` in `src/nebula/api/routes/admin.py` — the durable request-evidence seam for one persisted row
- `console/src/components/ledger/ledger-request-detail.tsx` — the authoritative request detail seam for explaining what remains historically true while a governed row still exists
- `src/nebula/services/governance_store.py` — the write-time and deletion-time seam that stamps and later removes governed rows using persisted markers such as `evidence_expires_at`
- `src/nebula/services/retention_lifecycle_service.py` — the runtime retention cleanup and `retention_lifecycle` health seam
- `console/src/app/(console)/observability/page.tsx` and runtime health surfaces — the corroboration layer that keeps health and dependency context subordinate to the selected request evidence
- `console/src/lib/hosted-contract.ts` and `console/src/app/trust-boundary/page.tsx` — the shared metadata-only trust-boundary vocabulary and public hosted disclosure seam
- `tests/test_governance_api.py`, `tests/test_retention_lifecycle_service.py`, `tests/test_health.py`, `tests/test_hosted_contract.py`, and focused console Vitest seams — the executable proof for persistence truth, deletion truth, health visibility, request-detail wording, and hosted metadata-only boundaries

Use this walkthrough when a reviewer needs one discoverable M008 story that proves tenant policy governs persistence and deletion, request detail stays historically truthful while a row exists, retention cleanup is visible as supporting runtime context, and the hosted plane remains metadata-only rather than a recovery or authority layer.

## What this integrated proof establishes

The M008 proof is complete only when one reviewer can inspect the shipped governance surfaces in order and reach the same narrow conclusion throughout:

1. tenant policy explicitly governs evidence retention and metadata minimization through the shipped policy/options and policy-form seams
2. one persisted usage-ledger row remains the primary request evidence while it still exists
3. request detail explains retained, suppressed, and deleted evidence truthfully from that persisted row instead of implying hidden archives or recovery behavior
4. governed deletion is driven by the row's persisted `evidence_expires_at`, not by a later guess about current tenant policy
5. `retention_lifecycle` health and Observability remain supporting runtime context for cleanup execution, not substitutes for request-level proof
6. the hosted plane does not receive raw usage-ledger rows and remains metadata-only rather than a request-level recovery or authority surface
7. the assembled proof stays inside the shipped governance boundary and does not imply a new compliance product, retention dashboard, hosted archive, or hosted runtime authority

If any step in this walkthrough starts implying row recovery after deletion, hosted raw-ledger export, or a new governance product scope beyond the shipped seams, the proof has drifted outside M008.

## Canonical proof order

Follow this sequence in order and keep each seam in its existing role.

### 1. Start with tenant policy and runtime-enforced evidence options

Begin with `GET /v1/admin/policy/options` in `src/nebula/api/routes/admin.py` and the operator editing surface in `console/src/components/policy/policy-form.tsx`.

This is the canonical entry seam for M008 because it makes the policy boundary explicit before any persisted request evidence is inspected. Reviewers should confirm here that Nebula keeps evidence governance narrow and operator-readable:

- tenant policy exposes `evidence_retention_window` as a runtime-enforced field
- tenant policy exposes `metadata_minimization_level` as a runtime-enforced field
- the policy form explains the effective evidence boundary in terms of what stays inspectable while a row exists and what minimization suppresses at write time
- the policy seam does not imply prompt capture, response capture, hosted authority, or a second governance workflow beyond the existing policy editor

The integrated proof starts here because later seams should reflect the policy boundary already set at write time instead of inventing a second explanation model.

### 2. Use one persisted row as the primary request evidence seam

Next inspect `GET /v1/admin/usage/ledger?request_id=...` in `src/nebula/api/routes/admin.py` and the selected-row explanation in `console/src/components/ledger/ledger-request-detail.tsx`.

This is the canonical request-evidence seam for M008. The proof should show that one persisted row remains the authoritative request record while it still exists. Reviewers should confirm that the row and request detail stay aligned on governed markers such as:

- `request_id`
- route and status metadata that were actually retained for that row
- `evidence_expires_at`
- `metadata_fields_suppressed`
- `governance_source`

This step matters because M008 does not prove evidence governance from policy copy alone. It proves that real request evidence is durably governed and still historically inspectable while the row exists.

### 3. Treat request detail as historically truthful while the row exists

Then continue in `console/src/components/ledger/ledger-request-detail.tsx` and the shared vocabulary in `console/src/lib/hosted-contract.ts`.

This is the canonical explanation seam for the retained-versus-suppressed-versus-deleted story. Reviewers should confirm that request detail preserves the same bounded reading throughout:

- retained request detail stays local to the persisted ledger row while that governed row still exists
- suppressed means governance removed or never wrote specific metadata fields, so those fields are no longer available later from the ledger
- deleted means governed retention removed the entire row at expiration; Nebula should not imply recovery, soft-delete archives, or hidden raw exports afterward
- supporting policy and health context may help interpret the request, but they do not replace the persisted row as the source of historical truth while that row still exists

The wording boundary is critical here. M008 succeeds only if request detail remains truthful about what the row still proves and equally truthful about what governance has already suppressed or deleted.

### 4. Confirm deletion is driven by persisted `evidence_expires_at`

After the persisted row story is clear, inspect `src/nebula/services/governance_store.py`, `src/nebula/services/retention_lifecycle_service.py`, and the focused backend seams in `tests/test_governance_api.py` and `tests/test_retention_lifecycle_service.py`.

This is the canonical deletion seam for M008. The proof should show that cleanup uses the row's persisted `evidence_expires_at` marker rather than inferring expiration later from current tenant policy. Reviewers should confirm that:

- governed rows are stamped with `evidence_expires_at` when they are written
- cleanup deletes rows whose persisted expiration marker has passed
- rows without an expiration marker are not treated as expired by guesswork
- post-cleanup inspection truth changes because the row is gone, not because the UI chose softer wording

This matters because the M008 story is about historically truthful evidence. A deleted row should disappear because governed retention removed it, not because Nebula preserved a hidden recovery layer.

### 5. Use `retention_lifecycle` health and Observability as supporting runtime context

Next inspect `src/nebula/services/retention_lifecycle_service.py`, `/health/ready`, `/health/dependencies`, and `console/src/app/(console)/observability/page.tsx`.

These are the canonical runtime-context seams for M008. They should show that retention execution is visible without becoming a replacement proof source. Reviewers should confirm the hierarchy stays explicit:

- `retention_lifecycle` appears in dependency health as an optional runtime surface
- readiness and dependency payloads report cleanup status, last run, and failure state as operational context
- Observability can surface that health context for investigation sequencing
- health and Observability do not replace `GET /v1/admin/usage/ledger?request_id=...` or request detail as the primary request-evidence path

This step is important because the integrated proof should make later drift obvious: if runtime health starts being described as more authoritative than the selected request evidence, the proof has widened beyond scope.

### 6. Finish with the hosted metadata-only trust boundary

Finally inspect `console/src/lib/hosted-contract.ts`, `console/src/app/trust-boundary/page.tsx`, and `tests/test_hosted_contract.py`.

This closes the M008 proof because it keeps the hosted plane in its existing bounded role. Reviewers should confirm that the hosted story stays narrow:

- hosted remains metadata-only by default
- hosted does not receive raw usage-ledger rows
- hosted trust-boundary wording continues to redirect request-level investigation back to the local runtime and local ledger surfaces
- hosted freshness and posture may help operators prioritize investigation, but they do not recover deleted rows, replace request detail, or become local runtime authority

The integrated proof is only complete when the hosted seam still reads as `notHosted`: the hosted control plane does not receive raw usage-ledger rows and cannot replace the local row as request-level evidence.

## How the canonical sources fit together

Use this map when deciding which source to open for detail.

| Need | Canonical source | Why it stays separate |
|---|---|---|
| Runtime-enforced evidence-governance fields | `GET /v1/admin/policy/options` in `src/nebula/api/routes/admin.py` | Keeps the policy capability boundary tied to the shipped admin route |
| Operator explanation of the effective evidence boundary | `console/src/components/policy/policy-form.tsx` | Keeps retention/minimization consequences anchored to the shipped form instead of a second governance spec |
| Durable per-request evidence while the row exists | `GET /v1/admin/usage/ledger?request_id=...` in `src/nebula/api/routes/admin.py` | Keeps request-level truth anchored to the shipped ledger route |
| Historically truthful explanation of retained/suppressed/deleted evidence | `console/src/components/ledger/ledger-request-detail.tsx` and `console/src/lib/hosted-contract.ts` | Keeps request-detail wording aligned with the shared evidence vocabulary |
| Write-time markers and deletion by persisted expiration | `src/nebula/services/governance_store.py` | Keeps retention semantics grounded in the shipped persistence layer |
| Runtime cleanup execution and dependency visibility | `src/nebula/services/retention_lifecycle_service.py`, `/health/ready`, and `/health/dependencies` | Keeps operational lifecycle truth separate from request-level historical evidence |
| Hosted metadata-only boundary | `console/src/lib/hosted-contract.ts`, `console/src/app/trust-boundary/page.tsx`, and `tests/test_hosted_contract.py` | Keeps hosted wording schema-backed, shared, and explicitly non-authoritative |
| Executable integrated-governance proof | focused pytest and Vitest seams for governance, retention lifecycle, health, request detail, and trust boundary | Keeps the close-out story grounded in code-backed verification rather than prose alone |

## Minimal operator walkthrough

Use this concise path when you need the full M008 proof in one review sequence:

1. Start in `GET /v1/admin/policy/options` and `console/src/components/policy/policy-form.tsx` to confirm tenant policy governs evidence retention and metadata minimization.
2. Inspect one persisted request through `GET /v1/admin/usage/ledger?request_id=...`.
3. Open the same request in `console/src/components/ledger/ledger-request-detail.tsx` and confirm request detail stays historically truthful while the row exists.
4. Confirm the retained, suppressed, deleted, and not-hosted vocabulary still matches `console/src/lib/hosted-contract.ts`.
5. Inspect `src/nebula/services/governance_store.py` and `src/nebula/services/retention_lifecycle_service.py` to confirm deletion is driven by persisted `evidence_expires_at` markers.
6. Use `/health/ready`, `/health/dependencies`, and Observability to confirm `retention_lifecycle` remains visible as supporting runtime context.
7. Open the hosted trust-boundary surfaces and confirm hosted remains metadata-only and cannot replace the local row as request-level evidence.
8. Use the focused pytest and Vitest seams as code-backed confirmation that the assembled policy, ledger, deletion, health, request detail, and hosted story still holds in the shipped worktree.

That is Nebula's canonical integrated M008 proof path.

## What this walkthrough intentionally does not duplicate

This document should not become a second governance contract, retention runbook, UI spec, or hosted export reference.

It intentionally does not restate:

- the full policy-options response shape already implemented in `src/nebula/api/routes/admin.py`
- the complete policy editor behavior and copy already shipped in `console/src/components/policy/policy-form.tsx`
- the full usage-ledger response model already implemented in `src/nebula/api/routes/admin.py` and related governance models
- the complete request-detail rendering behavior already implemented in `console/src/components/ledger/ledger-request-detail.tsx`
- the full write/delete implementation details already present in `src/nebula/services/governance_store.py`
- the full cleanup-loop and health payload details already implemented in `src/nebula/services/retention_lifecycle_service.py`
- the full hosted contract and schema-backed wording already defined in `console/src/lib/hosted-contract.ts` and related trust-boundary surfaces
- the full focused assertions already encoded in the relevant pytest and Vitest files

If one of those details changes, update the canonical source rather than copying replacement detail into this walkthrough.

## Failure modes this integrated proof makes obvious

These failure modes are the review shortcuts that reveal integrated-governance drift before a reviewer has to infer it from scattered code and test files.

The integrated proof has failed if any of these become true:

- tenant policy no longer reads as the first proof step for evidence governance
- `evidence_retention_window` or metadata-minimization consequences stop being explicit in the policy/options and policy-form seams
- `GET /v1/admin/usage/ledger?request_id=...` is omitted, replaced, or no longer treated as the primary request evidence while the row exists
- request detail stops presenting the persisted row as historically truthful while it still exists
- deletion stops reading as governed removal of the whole row and starts implying soft-delete archives, recovery, or hidden raw exports afterward
- cleanup stops being tied to persisted `evidence_expires_at` and starts depending on current-policy inference alone
- `retention_lifecycle` health stops being visible as supporting runtime context or starts being described as more authoritative than the selected request evidence
- hosted wording stops being metadata-only, starts implying raw usage-ledger export, or starts implying hosted recovery or runtime authority
- the walkthrough starts implying a broader governance dashboard, hosted archive, or compliance product not already present in the shipped seams

## Related docs and code-backed seams

- `src/nebula/api/routes/admin.py` — policy/options and usage-ledger admin seams
- `console/src/components/policy/policy-form.tsx` — effective evidence-boundary explanation seam
- `console/src/components/ledger/ledger-request-detail.tsx` — authoritative request-detail seam while the row exists
- `src/nebula/services/governance_store.py` — governed persistence and deletion markers
- `src/nebula/services/retention_lifecycle_service.py` — retention cleanup execution and health seam
- `console/src/app/(console)/observability/page.tsx` — supporting runtime-health and request investigation composition
- `console/src/lib/hosted-contract.ts` — shared retained/suppressed/deleted/not-hosted vocabulary
- `console/src/app/trust-boundary/page.tsx` — public hosted metadata-only disclosure seam
- `tests/test_governance_api.py` — persisted row and deletion semantics proof
- `tests/test_retention_lifecycle_service.py` — cleanup and failure-path proof
- `tests/test_health.py` — `retention_lifecycle` health visibility proof
- `tests/test_hosted_contract.py` — hosted metadata-only and coarse dependency-summary proof
