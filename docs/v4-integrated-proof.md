# v4 integrated proof

This document is Nebula's canonical integrated walkthrough for the v4 decisioning proof.

It assembles the already-shipped v4 seams into one strict review path without redefining their contracts, replaying their detailed operator copy, or implying broader product scope. Keep these sources in their canonical roles:

- [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md) — stable route signals, reason codes, and policy-outcome fragments
- [`docs/policy-guardrails.md`](policy-guardrails.md) — hard-budget and soft-budget explanation boundaries plus operator inspection surfaces
- [`docs/evaluation.md`](evaluation.md) — benchmark and evaluation entrypoints, artifact expectations, and proof-reading guidance
- `console/src/components/policy/policy-form.tsx` — policy preview-before-save and runtime-enforced cache/guardrail editing surface
- `src/nebula/api/routes/admin.py` — admin routes for policy simulation replay, recommendations, policy options, and usage-ledger inspection
- `src/nebula/services/recommendation_service.py` — bounded, read-only recommendation and cache-summary derivation from policy, ledger, and coarse runtime health
- `console/src/app/(console)/observability/page.tsx` — persisted ledger, recommendation, cache-summary, and dependency-health inspection surface
- `src/nebula/models/governance.py` — the typed response shapes that keep simulation, recommendation, cache, and ledger evidence operator-facing and interpretable

Use this walkthrough when a reviewer needs one discoverable v4 story that proves simulation, hard guardrails, grounded recommendations, cache controls, Observability framing, and benchmark artifacts agree without widening Nebula beyond operator-driven decisioning.

## What this integrated proof establishes

The v4 proof is complete only when one operator can inspect the shipped decisioning surfaces in order and reach the same narrow conclusion throughout:

1. routing explanations use a stable vocabulary rather than opaque heuristics
2. policy changes can be previewed against recent ledger-backed traffic before save
3. hard budget guardrails change live routing behavior explicitly, while soft budget remains advisory only
4. recommendations stay grounded in recent tenant evidence and remain bounded operator guidance rather than autonomous optimization
5. semantic-cache controls remain runtime-enforced policy settings with separate inspection-only summaries
6. Observability remains the persisted corroboration surface for ledger evidence, recommendation summaries, cache posture, and dependency context
7. benchmark artifacts remain the package-level proof that the same decisioning story produces legible route, cache, fallback, and cost evidence under repeatable scenarios

If any step in this walkthrough starts implying new hosted authority, new public APIs, billing expansion, SDK expansion, or autonomous platform behavior, the proof has drifted outside the v4 scope.

## Canonical proof order

Follow this sequence in order and keep each seam in its existing role.

### 1. Start with the route-decision vocabulary

Begin with [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md).

This document is the stable explanation seam for v4 because it defines the route signals, reason codes, and policy-outcome fragments that simulation replay, ledger inspection, and operator-facing UI surfaces must continue to reuse. Reviewers should confirm here that Nebula's routing story stays interpretable:

- signals are named and typed
- score is presented as an audit artifact, not an autonomous policy engine
- reason codes remain explicit and operator-readable
- policy-outcome fragments stay within decisioning scope and do not turn into a separate billing or analytics subsystem

The integrated proof starts here because later surfaces should point back to this vocabulary instead of inventing new explanation language.

### 2. Use policy preview replay before save

Next inspect the policy preview path documented in [`docs/policy-guardrails.md`](policy-guardrails.md), implemented in `console/src/components/policy/policy-form.tsx`, and backed by `POST /v1/admin/tenants/{tenant_id}/policy/simulate` in `src/nebula/api/routes/admin.py`.

This is the canonical preview seam for v4. The proof should show that operators can replay a candidate policy against recent ledger-backed traffic before saving it, then inspect:

- evaluated requests in the replay window
- changed routes
- newly denied requests
- premium cost delta
- compact changed-request samples and approximation notes

Keep two constraints explicit at this step:

- preview is evidence-only and does not save the policy
- the replay path depends on existing ledger history plus stable route/policy vocabulary rather than inventing new policy-authoring abstractions

This matters because the v4 proof is supposed to demonstrate controlled operator review, not hidden optimization loops.

### 3. Confirm hard guardrails and advisory budget signals stay distinct

Then return to [`docs/policy-guardrails.md`](policy-guardrails.md) and verify the same distinction is preserved in `console/src/components/policy/policy-form.tsx` and the `TenantPolicy` / `PolicyOptionsResponse` models in `src/nebula/models/governance.py`.

The integrated proof is only valid if reviewers can see that:

- hard cumulative budget controls are runtime-enforced guardrails
- hard-budget enforcement remains limited to the shipped `downgrade` or `deny` behaviors
- soft budget remains advisory only and does not deny, downgrade, or reroute on its own
- policy outcomes use stable explanatory fragments instead of inventing a new spend-reporting surface

At this seam, the operator should understand exactly which controls alter live request handling and which controls only attach advisory metadata.

### 4. Read recommendations and cache posture as bounded operator guidance

After policy replay and guardrails are clear, inspect `GET /v1/admin/tenants/{tenant_id}/recommendations` in `src/nebula/api/routes/admin.py`, the derivation rules in `src/nebula/services/recommendation_service.py`, and the recommendation plus semantic-cache summary section in `console/src/app/(console)/observability/page.tsx`.

This step should prove that the recommendation story stays narrow:

- recommendations are derived from recent ledger-backed traffic, current tenant policy, and coarse semantic-cache runtime health
- recommendation cards are deterministic, tenant-scoped, and read-only
- cache posture is summarized separately from policy editing
- the Observability page stays inspection-only for recommendations and cache summary, redirecting operators back to the existing policy editor for changes

The wording here matters. Recommendations are grounded, bounded, and operator-driven. They are not black-box optimization, autonomous tuning, or self-applying policy changes.

### 5. Use Observability as the persisted corroboration surface

Next inspect `console/src/app/(console)/observability/page.tsx` together with `GET /v1/admin/usage/ledger` in `src/nebula/api/routes/admin.py`.

Observability closes the runtime proof path because it assembles the persisted request evidence and the supporting v4 summaries in one operator-facing inspection surface. Reviewers should confirm the page preserves this hierarchy:

- the usage ledger remains the persisted request-evidence source
- request detail remains the inspection path for final route, provider, fallback, and policy evidence
- recommendation summaries and semantic-cache summaries are supporting context for the same tenant investigation
- dependency health adds runtime context but does not replace ledger evidence

This step is important because the integrated proof should make later drift obvious: if Observability starts reading like a new control plane, a new dashboard concept, or a substitute for the underlying ledger and policy surfaces, the proof has widened beyond scope.

### 6. Finish with benchmark and evaluation artifacts

Finally, validate the package-level proof using [`docs/evaluation.md`](evaluation.md).

The benchmark walkthrough is the last step because it demonstrates that the same narrow decisioning story remains visible under repeatable scenario suites. Reviewers should use the documented entrypoints and artifact expectations to confirm:

- route target, provider, cache-hit, fallback, latency, and estimated premium cost stay explicit in the output
- summary-first reporting makes savings, route mix, and fallback behavior legible before raw tables
- expectation mismatches are surfaced rather than hidden
- cost evidence remains estimate-based proof material, not invoice reconciliation or a broader billing system

This closes the integrated v4 path by showing that the shipped decisioning seams also hold together in repeatable benchmark evidence.

## How the canonical sources fit together

Use this map when deciding which source to open for detail.

| Need | Canonical source | Why it stays separate |
|---|---|---|
| Stable route signals, reason codes, and policy-outcome vocabulary | [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md) | Prevents explanation drift across replay, ledger, and UI surfaces |
| Hard-budget and soft-budget semantics plus operator inspection framing | [`docs/policy-guardrails.md`](policy-guardrails.md) | Keeps guardrail semantics and scope limits from being restated inconsistently |
| Replay-before-save API seam, recommendation endpoint, and ledger inspection routes | `src/nebula/api/routes/admin.py` | Keeps the concrete admin capability boundary tied to shipped routes |
| Typed policy, simulation, recommendation, cache, and ledger shapes | `src/nebula/models/governance.py` | Keeps operator evidence shapes explicit and interpretable |
| Bounded recommendation and cache-summary derivation logic | `src/nebula/services/recommendation_service.py` | Keeps recommendation behavior grounded in deterministic code, not prose claims |
| Policy editing and simulation preview UI | `console/src/components/policy/policy-form.tsx` | Keeps the authoring and preview workflow anchored to the shipped console surface |
| Persisted ledger plus supporting runtime context | `console/src/app/(console)/observability/page.tsx` | Keeps the joined inspection story tied to the real operator-facing surface |
| Repeatable benchmark and artifact-reading guidance | [`docs/evaluation.md`](evaluation.md) | Keeps package-level proof and artifact interpretation in one place |

## Minimal operator walkthrough

Use this concise path when you need the full v4 proof in one review sequence:

1. Start in [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md) and confirm the stable route signals, reason codes, and policy-outcome fragments.
2. Open [`docs/policy-guardrails.md`](policy-guardrails.md) to confirm the intended distinction between hard guardrails and soft budget advisory.
3. In `console/src/components/policy/policy-form.tsx`, review the preview-before-save path and the runtime-enforced cache and budget controls.
4. In `src/nebula/api/routes/admin.py`, confirm the shipped admin seams for policy simulation replay, recommendations, and usage-ledger inspection.
5. In `src/nebula/services/recommendation_service.py`, confirm recommendations remain deterministic, read-only, and grounded in ledger, policy, and cache runtime evidence.
6. In `console/src/app/(console)/observability/page.tsx`, confirm the persisted ledger remains the primary request-evidence surface, while recommendations, cache posture, and dependency health remain supporting context.
7. In [`docs/evaluation.md`](evaluation.md), use the benchmark entrypoints and artifact expectations to confirm the route, cache, fallback, and estimated-cost story still holds under repeatable evaluation.

That is Nebula's canonical integrated v4 proof path.

## What this walkthrough intentionally does not duplicate

This document should not become a second policy contract, admin API reference, UI spec, or benchmark runbook.

It intentionally does not restate:

- the detailed route vocabulary already defined in [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md)
- the complete hard-budget and soft-budget semantics already defined in [`docs/policy-guardrails.md`](policy-guardrails.md)
- the full request and response shapes already defined in `src/nebula/models/governance.py`
- the complete admin implementation details already present in `src/nebula/api/routes/admin.py`
- the full recommendation heuristics and cache-summary derivation details already implemented in `src/nebula/services/recommendation_service.py`
- the full console copy and component behavior already shipped in `console/src/components/policy/policy-form.tsx` and `console/src/app/(console)/observability/page.tsx`
- the benchmark invocation details and artifact interpretation guidance already documented in [`docs/evaluation.md`](evaluation.md)

If one of those details changes, update the canonical source rather than copying replacement detail into this walkthrough.

## Failure modes this integrated proof makes obvious

This walkthrough is useful because it makes v4 scope drift and proof drift visible.

The integrated proof has failed if any of these become true:

- route explanations no longer point back to the stable vocabulary in [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md)
- policy preview no longer replays recent ledger-backed traffic before save, or starts behaving like an implicit save path
- hard guardrails and soft budget advisory are no longer clearly separated
- recommendations stop reading as grounded, bounded, operator-driven guidance and start implying autonomous optimization or self-applying policy changes
- semantic-cache summaries stop pointing back to runtime-enforced policy controls and instead imply a separate cache-management subsystem
- Observability is described as a new authority surface instead of persisted corroboration for ledger evidence plus supporting runtime context
- benchmark artifacts stop exposing route, cache, fallback, and estimated-cost evidence clearly, or start implying invoice-grade billing authority
- the walkthrough introduces new API surfaces, new dashboard concepts, billing analytics expansion, SDK promises, or hosted-plane authority not already present in the shipped v4 seams

## Related docs and code-backed seams

- [`docs/route-decision-vocabulary.md`](route-decision-vocabulary.md) — stable route explanation seam
- [`docs/policy-guardrails.md`](policy-guardrails.md) — hard-budget and soft-budget boundary
- [`docs/evaluation.md`](evaluation.md) — benchmark entrypoints and artifact-reading guide
- `console/src/components/policy/policy-form.tsx` — policy preview and runtime-enforced controls
- `src/nebula/api/routes/admin.py` — simulation, recommendation, and usage-ledger admin surfaces
- `src/nebula/services/recommendation_service.py` — bounded recommendation derivation
- `console/src/app/(console)/observability/page.tsx` — persisted request evidence plus supporting context
- `src/nebula/models/governance.py` — typed governance and operator-evidence shapes
