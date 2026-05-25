# M010 integrated resilience proof

This document is Nebula's canonical pointer-first walkthrough for the M010 integrated resilience proof.

It assembles the already-shipped outage, operator-inspection, and recovery seams into one strict review path without redefining their field contracts, inventing a new resilience surface, or widening hosted/control-plane scope. Keep these sources in their canonical roles:

- [`docs/hosted-reinforcement-boundary.md`](hosted-reinforcement-boundary.md) — the controlling trust-boundary document for any hosted or control-plane wording; local runtime proof remains authoritative
- [`docs/m009-integrated-proof.md`](m009-integrated-proof.md) — the established integrated-proof pattern for pointer-first review order and anti-duplication boundaries
- [`docs/m010-recovery-proof.md`](m010-recovery-proof.md) — the bounded recovery walkthrough for outage-to-recovery truth across existing runtime and console surfaces
- `/health/ready` in `src/nebula/main.py` — the canonical serving-readiness seam for overall ready, degraded, and not-ready truth
- `/health/dependencies` in `src/nebula/main.py` — the canonical dependency-truth seam for dependency class, lifecycle state, serving effect, `recovering`, and incident timestamps
- `tests/test_phase10_outage_safety.py` — the deterministic outage and recovery proof seam for governance-store fail-closed behavior, semantic-cache degraded continuity, premium-provider degraded continuity, hosted metadata continuity, and both recovery transitions
- `tests/test_health.py` — focused health-contract coverage for degraded and recovering dependency semantics
- `console/src/app/(console)/observability/page.tsx` — the selected-request-first operator surface where dependency health remains supporting runtime context instead of replacing request evidence
- `console/src/components/health/runtime-health-cards.tsx` — the operator-visible dependency metadata surface for lifecycle state, serving effect, `recovering`, `last_failure_at`, and `last_recovery_at`

Use this walkthrough when a reviewer needs one discoverable M010 story that proves, in order:

1. local runtime health is the first outage and recovery authority
2. the bounded outage classes from S02 and S06 remain truthful and intentionally different
3. the existing Observability and runtime health card seams from S03 let operators inspect that same truth without creating a new authority layer
4. the recovery proof from [`docs/m010-recovery-proof.md`](m010-recovery-proof.md) and the deterministic seams from S04 close the loop on restored healthy behavior
5. hosted or control-plane language remains subordinate to local-runtime truth throughout

## What this integrated proof establishes

The M010 integrated resilience proof is complete only when one reviewer can inspect the existing seams in order and reach the same narrow conclusion throughout:

1. local runtime truth on `/health/ready` and `/health/dependencies` is the first authority for outage classification and recovery confirmation
2. governance-store outage is serving-critical and must fail closed until the health surfaces say it is actually ready again
3. semantic-cache outage is serving-optional and must remain visible as degraded continuity without blocking otherwise healthy local serving
4. Observability and runtime health cards corroborate the same runtime truth as supporting operator surfaces without replacing selected-request-first evidence
5. recovery is proved through the same existing health and serving seams rather than by a new dashboard, manual narrative, or hosted status summary
6. hosted/control-plane wording stays descriptive only and never becomes serving-time authority
7. the proof path remains pointer-first: this document tells reviewers where to look and in what order instead of restating endpoint contracts, UI field contracts, or test implementation details already owned elsewhere

If any step in this walkthrough starts treating hosted freshness as serving truth, skipping local health surfaces, collapsing fail-closed and degraded outage classes into one story, or turning Observability into a new resilience product, the proof has drifted outside M010.

## Canonical proof order

Follow this sequence in order and keep each seam in its existing role.

### 1. Start with the local-authority trust boundary

Begin with [`docs/hosted-reinforcement-boundary.md`](hosted-reinforcement-boundary.md).

This matters because M010 resilience proof is intentionally local-authority-first. Before inspecting any outage or recovery behavior, reviewers should confirm that:

- hosted surfaces are metadata-backed and descriptive only
- the hosted plane is not in the request-serving path
- hosted freshness or posture is not authoritative serving-time health
- serving-time outage and recovery truth must be confirmed from the local runtime and its shipped operator surfaces

This first step prevents the rest of the walkthrough from drifting into control-plane authority or a broader incident-management story.

### 2. Classify the outage from `/health/ready` and `/health/dependencies`

Next inspect `/health/ready` and `/health/dependencies`.

These are the canonical runtime truth seams for M010 because they establish whether Nebula is ready, degraded, or not ready and explain the serving consequence of each dependency state. For this proof, reviewers should use them first to confirm:

- overall readiness state (`ready`, `degraded`, `not_ready`)
- per-dependency `status`
- `dependency_class`
- `lifecycle_state`
- `serving_effect`
- `reason_code`
- `recovering`
- `last_failure_at`
- `last_recovery_at`

The outage classes already proved in M010 must remain clearly distinct here:

- **governance_store** is serving-critical and must surface fail-closed truth; when it is `not_ready` or `recovering`, `/health/ready` must not claim global readiness
- **semantic_cache** is serving-optional and must surface degraded continuity truth; when it is degraded or recovering, `/health/ready` may remain 200 while dependency metadata still explains reduced capability
- **premium_provider** is serving-optional and must surface degraded continuity truth without blocking unrelated healthy local serving paths when Nebula can still route locally
- **hosted metadata services** are metadata-only and must not become serving-time authority; outage evidence may appear in administrative or logged supporting seams, but local request serving and readiness must remain governed by runtime-serving dependencies

If a reviewer cannot tell from these endpoints alone whether the system should fail closed or continue in degraded mode, the integrated proof is incomplete before any operator surface is opened.

### 3. Confirm serving consequences on the real request path

After the health surfaces classify the outage, confirm the serving consequence on the real request path using the deterministic seams in `tests/test_phase10_outage_safety.py`.

These executable seams prove the bounded outage classes that the integrated review depends on:

- **governance-store outage**: `POST /v1/chat/completions` fails closed with `503` and `{"detail": "Governance store unavailable."}` while readiness is `not_ready`
- **semantic-cache outage**: `POST /v1/chat/completions` still succeeds on the healthy local path while readiness and dependency health remain explicitly degraded for the optional dependency
- **premium-provider outage**: `POST /v1/chat/completions` can still succeed on the healthy local path while `/health/ready` and `/health/dependencies` report `premium_provider` as degraded continuity-limited rather than falsely healthy or globally blocking
- **hosted metadata outage**: hosted heartbeat / remote-management failure remains visible in supporting seams without blocking local request serving or promoting hosted status into readiness authority

This step matters because M010 is not just a health-endpoint documentation exercise. It proves that runtime truth and serving behavior agree for both outage classes.

### 4. Use Observability and runtime health cards as operator corroboration

Next inspect the shipped console surfaces:

- `console/src/app/(console)/observability/page.tsx`
- `console/src/components/health/runtime-health-cards.tsx`

These are the canonical operator corroboration seams for M010. They do not replace runtime truth; they make the same runtime evidence inspectable inside the existing selected-request-first workflow.

Reviewers should confirm that:

- Observability still tells operators to inspect one persisted request first
- dependency health remains supporting context for that same investigation
- runtime health cards render the same bounded metadata needed to explain outage and recovery state, including lifecycle state, serving effect, `recovering`, `last_failure_at`, and `last_recovery_at`
- optional dependency degradation is visible without claiming it blocks gateway readiness
- no new outage-specific dashboard, resilience console, or hosted authority surface was introduced to tell this story

This step preserves R088's operator-surface role while keeping operator inspection subordinate to the local-runtime authority boundary.

### 5. Return to the same runtime surfaces for recovery truth

After the outage and operator corroboration path is clear, use [`docs/m010-recovery-proof.md`](m010-recovery-proof.md) and the same `/health/ready` plus `/health/dependencies` seams to confirm recovery.

The integrated proof depends on the bounded recovery rules already established there:

- governance recovery is complete only when the serving-critical dependency returns to `ready`, `/health/ready` returns `200`, and chat completions succeed again
- semantic-cache recovery is complete only when degraded truth moves through `recovering` to `ready` on the same dependency-health surfaces while serving remains truthful throughout
- `recovering`, `last_failure_at`, and `last_recovery_at` are supporting evidence that supersede stale outage state instead of hiding it

This step is intentionally pointer-first: use the dedicated recovery document for the bounded transition details rather than duplicating them here.

### 6. Finish with the deterministic anti-drift seams from S04

Finally inspect the focused executable seams that keep the assembled proof honest:

- `tests/test_phase10_outage_safety.py`
- `tests/test_health.py`

Together these tests are the anti-drift proof for M010 because they keep the narrative grounded in shipped behavior. Reviewers should confirm they still cover:

- governance fail-closed outage truth
- governance recovery back to successful serving and ready health
- semantic-cache degraded continuity during outage
- semantic-cache recovery through `recovering` to `ready`
- premium-provider degraded continuity during outage without blocking unrelated healthy local serving
- hosted metadata outage continuity that remains non-authoritative for serving readiness
- degraded versus recovering readiness semantics for optional and serving-critical dependencies

This is the close-out step because M010's integrated resilience proof is only strong when its outage, operator inspection, and recovery seams remain executable rather than prose-only.

## How the canonical sources fit together

| Need | Canonical source | Why it stays separate |
|---|---|---|
| Hosted/control-plane boundary | [`docs/hosted-reinforcement-boundary.md`](hosted-reinforcement-boundary.md) | Prevents the walkthrough from implying hosted serving-time authority |
| Pointer-first integrated review pattern | [`docs/m009-integrated-proof.md`](m009-integrated-proof.md) | Prevents this document from becoming a second contract or duplicating prior integrated-proof structure |
| Bounded outage-to-recovery transition details | [`docs/m010-recovery-proof.md`](m010-recovery-proof.md) | Prevents this document from cloning the dedicated recovery walkthrough |
| Overall serving-readiness truth | `/health/ready` in `src/nebula/main.py` | Keeps runtime readiness proof tied to the shipped endpoint |
| Dependency-specific outage and recovery truth | `/health/dependencies` in `src/nebula/main.py` | Keeps dependency class, lifecycle, serving effect, and timestamps anchored to the shipped backend surface |
| Deterministic outage and recovery behavior | `tests/test_phase10_outage_safety.py` | Keeps the integrated proof grounded in executable runtime behavior |
| Focused degraded and recovering health semantics | `tests/test_health.py` | Keeps readiness aggregation and dependency-state interpretation stable |
| Selected-request-first operator framing | `console/src/app/(console)/observability/page.tsx` | Keeps dependency health subordinate to request investigation |
| Operator-visible dependency metadata | `console/src/components/health/runtime-health-cards.tsx` | Keeps outage and recovery state inspectable without inventing a new UI surface |

## Minimal reviewer and operator walkthrough

Use this concise path when you need the full M010 integrated resilience proof in one review sequence:

1. Read [`docs/hosted-reinforcement-boundary.md`](hosted-reinforcement-boundary.md) and confirm hosted remains descriptive only.
2. Open `/health/ready` and `/health/dependencies` and classify the incident from local runtime truth first.
3. Confirm which outage class is in play: governance-store must fail closed; semantic-cache must remain visible as degraded continuity.
4. Use `tests/test_phase10_outage_safety.py` to confirm the real request path matches that classification.
5. Open Observability and runtime health cards and confirm operators can inspect the same dependency truth as supporting context without replacing selected-request-first evidence.
6. Follow [`docs/m010-recovery-proof.md`](m010-recovery-proof.md) to confirm the same shipped runtime surfaces also tell a truthful recovery story.
7. Use `tests/test_health.py` and the recovery-focused seams in `tests/test_phase10_outage_safety.py` as code-backed proof that degraded, recovering, and ready transitions still agree with the shipped health contract.

That is Nebula's canonical M010 integrated resilience proof path.

## What this walkthrough intentionally does not duplicate

This document does not duplicate the detailed health endpoint field contracts, the full recovery walkthrough, the full console component behavior, or the full test assertions it depends on.

It intentionally does not duplicate:

- the hosted/control-plane trust boundary already defined in [`docs/hosted-reinforcement-boundary.md`](hosted-reinforcement-boundary.md)
- the detailed outage-to-recovery transition walkthrough already defined in [`docs/m010-recovery-proof.md`](m010-recovery-proof.md)
- the full integrated-proof framing pattern already established by [`docs/m009-integrated-proof.md`](m009-integrated-proof.md)
- the complete `/health/ready` and `/health/dependencies` field contracts already owned by the runtime implementation and tests
- the full Observability and runtime-health-card rendering details already owned by the shipped console code
- the complete deterministic assertions already proven in `tests/test_phase10_outage_safety.py` and `tests/test_health.py`

If one of those details changes, update the canonical source rather than copying replacement detail here.

## Anti-duplication and anti-sprawl boundaries

This integrated proof stays in scope only if all of the following remain true:

- it points reviewers to existing runtime, console, and test seams instead of re-specifying them
- it treats local runtime truth as authoritative and console surfaces as corroborating inspection aids
- it does not imply a new resilience dashboard, incident workflow, or hosted operational authority
- it does not introduce new runtime telemetry, new response fields, or new operator UI features to make the proof legible
- it keeps governance fail-closed and semantic-cache degraded continuity as two bounded outage classes rather than a generalized outage taxonomy
- it keeps hosted/control-plane wording subordinate to the trust-boundary document instead of retelling that contract here

If a future change needs broader resilience scope, it should be proposed explicitly in a later milestone rather than implied through this close-out document.

## Failure modes this integrated proof makes obvious

These are the review shortcuts that reveal M010 drift quickly:

- `/health/ready` or `/health/dependencies` stop being the first authoritative outage and recovery proof step
- governance-store outage no longer fails closed on the serving path
- semantic-cache outage starts blocking otherwise healthy local serving paths or stops being visible as degraded continuity
- runtime health cards or Observability stop exposing the dependency metadata needed to inspect degraded, recovering, and ready states
- console surfaces start reading like a replacement authority layer instead of supporting selected-request-first investigation
- recovery is claimed from hosted status, dependency reachability alone, or manual narrative without matching runtime-health and serving evidence
- `recovering`, `last_failure_at`, or `last_recovery_at` disappear, contradict current state, or stop helping distinguish stale outage from restored service
- this document starts restating full endpoint contracts, UI contracts, or test contracts instead of pointing to their canonical sources
- the walkthrough starts implying a new resilience product, new dashboard, or broader hosted control not already shipped

## Related docs and code-backed seams

- [`docs/hosted-reinforcement-boundary.md`](hosted-reinforcement-boundary.md) — hosted trust boundary that remains subordinate to local runtime proof
- [`docs/m009-integrated-proof.md`](m009-integrated-proof.md) — pointer-first integrated-proof pattern reused here
- [`docs/m010-recovery-proof.md`](m010-recovery-proof.md) — bounded outage-to-recovery walkthrough for the same seams
- `src/nebula/main.py` — `/health/ready` and `/health/dependencies`
- `tests/test_phase10_outage_safety.py` — deterministic outage and recovery proofs
- `tests/test_health.py` — focused degraded and recovering health-contract coverage
- `console/src/app/(console)/observability/page.tsx` — selected-request-first operator framing
- `console/src/components/health/runtime-health-cards.tsx` — dependency lifecycle and recovery metadata rendering
