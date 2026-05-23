# M010 recovery proof

This document is Nebula's canonical bounded walkthrough for the M010 recovery proof.

It assembles the already-shipped outage and recovery seams into one pointer-first review path that starts with local runtime truth, confirms restored serving behavior, and closes with operator-visible recovery evidence. It does not introduce a new resilience product, a new dashboard, or hosted authority. Keep these sources in their canonical roles:

- [`docs/hosted-reinforcement-boundary.md`](hosted-reinforcement-boundary.md) — the controlling trust-boundary document for any hosted/control-plane wording; local runtime proof remains authoritative
- [`docs/m009-integrated-proof.md`](m009-integrated-proof.md) — the pointer-first integrated-proof pattern this document follows
- `/health/ready` in `src/nebula/main.py` — the canonical serving-readiness seam that shows whether Nebula is ready, degraded, or not ready
- `/health/dependencies` in `src/nebula/main.py` — the canonical dependency-truth seam that exposes dependency-specific lifecycle, serving effect, recovery state, and timestamps
- `tests/test_phase10_outage_safety.py` — the deterministic outage and recovery proof seam for governance-store fail-closed recovery and semantic-cache degraded recovery
- `tests/test_health.py` — focused health-contract coverage for degraded and recovering dependency states
- `console/src/app/(console)/observability/page.tsx` — the selected-request-first operator surface where dependency health stays supporting context instead of becoming the primary truth source
- `console/src/components/health/runtime-health-cards.tsx` — the operator-visible dependency metadata surface for lifecycle state, serving effect, recovering, `last_failure_at`, and `last_recovery_at`
- `console/src/lib/admin-api.ts` — the typed console contract for dependency health fields used by the existing operator surfaces
- [`.gsd/milestones/M010/M010-CONTEXT.md`](../.gsd/milestones/M010/M010-CONTEXT.md) and [`.gsd/milestones/M010/slices/S04/S04-RESEARCH.md`](../.gsd/milestones/M010/slices/S04/S04-RESEARCH.md) — the milestone boundary and slice rationale for why recovery proof must stay bounded to existing seams

Use this walkthrough when a reviewer needs one discoverable M010 story that proves:

1. a high-value outage class is visible on the existing health surfaces
2. Nebula either fails closed or continues in a bounded degraded mode truthfully during that outage
3. recovery changes the same truth surfaces instead of leaving stale incident state unexplained
4. restored healthy behavior is visible through the real serving path and the existing operator surfaces
5. hosted/control-plane language remains subordinate to local runtime evidence throughout

## What this recovery proof establishes

The M010 recovery proof is complete only when one reviewer can inspect the existing seams in order and reach the same narrow conclusion throughout:

1. local runtime and dependency health surfaces are the first source of outage truth
2. governance-store outage is treated as serving-critical and fails closed until recovery is complete
3. semantic-cache outage is treated as serving-optional and remains visible as degraded continuity until recovery is complete
4. recovery confirmation requires both restored behavior and truthful post-recovery evidence on the same shipped surfaces
5. `recovering`, `last_failure_at`, and `last_recovery_at` are supporting evidence that supersede stale outage state rather than hiding it
6. Observability and runtime-health cards stay supporting operator inspection seams under the selected-request-first workflow
7. hosted or control-plane context never becomes the authority for serving-time outage classification or recovery truth

If any step in this walkthrough starts treating a hosted surface as authoritative, invents a recovery-specific dashboard, skips local health evidence, or treats dependency reachability alone as sufficient proof of recovery, the recovery proof has drifted outside M010.

## Canonical proof order

Follow this sequence in order and keep each seam in its existing role.

### 1. Start with the local trust boundary and scope

Begin with [`docs/hosted-reinforcement-boundary.md`](hosted-reinforcement-boundary.md) and the M010 context in [`.gsd/milestones/M010/M010-CONTEXT.md`](../.gsd/milestones/M010/M010-CONTEXT.md).

This matters because M010 recovery proof is intentionally local-authority-first. Reviewers should confirm before reading anything else that:

- hosted surfaces are descriptive only
- hosted freshness or posture is not serving-time health truth
- recovery proof must be confirmed from local runtime and operator surfaces
- the goal is trustworthy outage and recovery inspection, not a broader incident-management product

This first step keeps the rest of the walkthrough from widening into hosted authority or a new dashboard story.

### 2. Inspect outage truth on `/health/ready` and `/health/dependencies`

Next inspect `/health/ready` and `/health/dependencies`.

These are the canonical runtime truth seams for M010 recovery proof. They already expose the dependency-specific fields that matter for outage and recovery review:

- overall status (`ready`, `degraded`, `not_ready`)
- per-dependency `status`
- `dependency_class`
- `lifecycle_state`
- `serving_effect`
- `reason_code`
- `recovering`
- `last_failure_at`
- `last_recovery_at`

Reviewers should use these endpoints to classify the incident before looking at any console surface.

For the highest-value outage classes currently proved in M010:

- **governance store** must read as serving-critical with `serving_effect: fail_closed`; if it is `not_ready` or `recovering`, `/health/ready` must not claim global readiness
- **semantic cache** must read as serving-optional with `serving_effect: continuity_limited`; when degraded or recovering, `/health/ready` may remain 200 while the dependency metadata still tells the truth about reduced capability

If these endpoints do not make the dependency class, lifecycle state, or serving effect obvious, the recovery proof is incomplete before any request or UI inspection begins.

### 3. Confirm outage behavior through the real serving path

After the health surfaces establish the outage state, confirm the serving consequence on the real request path.

The deterministic executable proof lives in `tests/test_phase10_outage_safety.py`, and it proves the two highest-value behaviors that the walkthrough depends on:

- **governance-store outage**: `POST /v1/chat/completions` fails closed with `503` and `{"detail": "Governance store unavailable."}` while `/health/ready` reports `not_ready`
- **semantic-cache outage**: `POST /v1/chat/completions` still succeeds on the healthy local path while `/health/ready` and `/health/dependencies` report degraded optional-dependency truth

This step matters because recovery is only meaningful relative to the correct outage behavior. A dependency cannot be said to have recovered if the outage behavior was already dishonest or ambiguous.

### 4. Use the same health surfaces to confirm recovery transitions

Once the outage state is clear, return to `/health/ready` and `/health/dependencies` to inspect recovery.

Recovery confirmation in M010 is not just “the dependency came back.” It requires the same shipped health surfaces to show that stale outage state has been superseded by current recovery or ready state.

The expected transition patterns are:

#### Governance-store recovery

The governance recovery proof in `tests/test_phase10_outage_safety.py` establishes this bounded story:

1. outage: governance reports `lifecycle_state: not_ready`, `serving_effect: fail_closed`, and `reason_code: governance_query_failed`
2. outage: `/health/ready` returns `503` with top-level `status: not_ready`
3. recovery complete: the same dependency reports `lifecycle_state: ready`, `reason_code: governance_ready`, and populated `last_failure_at` plus `last_recovery_at`
4. recovery complete: `/health/ready` returns `200` once the serving-critical dependency is actually ready again

This is the highest-value recovery proof because it demonstrates that a fail-closed dependency can return to truthful service without hiding the incident history.

#### Semantic-cache recovery

The semantic-cache recovery proof in `tests/test_phase10_outage_safety.py` establishes this bounded story:

1. outage: semantic cache reports `lifecycle_state: degraded` with `reason_code: semantic_cache_unavailable`
2. recovering: the same dependency reports `lifecycle_state: recovering`, `recovering: true`, and recovery timestamps while overall readiness may still be `degraded`
3. recovery complete: the dependency reports `lifecycle_state: ready`, `recovering: false`, and retained incident timestamps for operator context
4. recovery complete: overall runtime health returns to `ready` when no other dependency remains degraded

This step proves that “recovering” is not a cosmetic flag. It is an observable intermediate state that keeps reduced capability explicit until the dependency is actually ready.

### 5. Confirm post-recovery serving behavior, not just health metadata

After the health surfaces indicate recovery, confirm the serving path again.

What counts as recovery confirmation in M010 is:

- the dependency-specific health state has moved from outage or degraded truth to recovering or ready truth on the shipped health surfaces
- the serving path now behaves consistently with that updated state
- the timestamps and recovery metadata explain the incident instead of erasing it

For the current highest-value proofs:

- governance recovery is confirmed only when chat completions succeed again after the outage and the health surfaces no longer claim `not_ready`
- semantic-cache recovery is confirmed only when chat serving remains truthful through degraded and recovering phases and the dependency health eventually returns to `ready`

If request behavior and health metadata disagree after recovery, treat that as drift or stale failure state until proven otherwise.

### 6. Use Observability and runtime health cards as operator corroboration

Next inspect the existing console surfaces:

- `console/src/app/(console)/observability/page.tsx`
- `console/src/components/health/runtime-health-cards.tsx`
- `console/src/lib/admin-api.ts`

These are the canonical operator corroboration seams for M010 recovery proof. They do not replace the health endpoints; they make the same runtime evidence inspectable in the already-shipped operator workflow.

Reviewers should confirm that:

- Observability still frames the selected request as the primary evidence seam
- dependency health remains supporting context for that same investigation
- runtime health cards render lifecycle state, serving effect, reason code, `recovering`, `last_failure_at`, and `last_recovery_at`
- optional dependency degradation is visible without claiming it blocks gateway readiness

This step matters because S04 is supposed to leave behind an operator-usable recovery path, but the path must remain bounded to existing surfaces.

### 7. Finish with the executable anti-drift seams

Finally inspect the focused tests that keep this walkthrough honest:

- `tests/test_phase10_outage_safety.py`
- `tests/test_health.py`

These are the executable anti-drift seams for M010 recovery proof because they verify the outage, recovery, and timestamp story directly against the shipped runtime behavior rather than prose alone.

Reviewers should confirm they still cover:

- governance fail-closed outage truth
- governance recovery back to successful serving and ready health
- semantic-cache degraded continuity during outage
- semantic-cache recovery through `recovering` to `ready`
- health-contract handling for recovering optional and serving-critical dependencies

## How the canonical sources fit together

| Need | Canonical source | Why it stays separate |
|---|---|---|
| Hosted/control-plane boundary | [`docs/hosted-reinforcement-boundary.md`](hosted-reinforcement-boundary.md) | Prevents recovery proof from implying hosted authority |
| Pointer-first proof pattern | [`docs/m009-integrated-proof.md`](m009-integrated-proof.md) | Prevents this document from turning into a second contract or a full runbook clone |
| Runtime readiness truth | `/health/ready` in `src/nebula/main.py` | Keeps serving-readiness proof tied to the shipped endpoint |
| Dependency-specific outage and recovery truth | `/health/dependencies` in `src/nebula/main.py` | Keeps lifecycle, serving effect, and timestamps anchored to the shipped dependency surface |
| Deterministic outage and recovery behavior | `tests/test_phase10_outage_safety.py` | Keeps the walkthrough grounded in executable end-to-end proof |
| Focused readiness and recovery aggregation contract | `tests/test_health.py` | Keeps degraded versus recovering semantics stable |
| Operator-visible dependency evidence | `console/src/components/health/runtime-health-cards.tsx` | Keeps recovery metadata inspectable without inventing new UI |
| Selected-request-first operator framing | `console/src/app/(console)/observability/page.tsx` | Keeps dependency health subordinate to the request investigation |
| Typed console dependency contract | `console/src/lib/admin-api.ts` | Keeps operator surfaces aligned with the shipped runtime fields |

## Minimal operator walkthrough

Use this concise path when you need the full bounded M010 recovery proof in one review sequence:

1. Read [`docs/hosted-reinforcement-boundary.md`](hosted-reinforcement-boundary.md) to confirm hosted remains descriptive only.
2. Open `/health/ready` and `/health/dependencies` and classify the incident from local runtime truth first.
3. For governance outage, confirm fail-closed behavior: `POST /v1/chat/completions` returns `503` and readiness is `not_ready`.
4. For semantic-cache outage, confirm bounded degraded behavior: chat still succeeds while dependency health reports degraded optional-dependency truth.
5. After recovery action, inspect `/health/dependencies` again and confirm the dependency has moved to `recovering` or `ready` with truthful timestamps.
6. Confirm `/health/ready` has changed consistently with the dependency class: serving-critical recovery must restore readiness only when actually ready; serving-optional recovery may pass through degraded first.
7. Confirm the serving path now matches the recovered health state.
8. Open Observability and the runtime health cards to confirm the same dependency metadata is operator-visible on existing surfaces.
9. Use `tests/test_phase10_outage_safety.py` and `tests/test_health.py` as code-backed proof that the outage and recovery story still holds in the shipped worktree.

That is Nebula's canonical bounded M010 recovery proof path.

For the higher-level close-out review order that joins this recovery walkthrough with outage classification and operator corroboration on the same existing surfaces, see [`docs/m010-integrated-proof.md`](m010-integrated-proof.md).

## What counts as recovery confirmation

M010 recovery is confirmed only when all of the following are true:

- the relevant dependency moved from outage or degraded state to recovering or ready state on the existing health surfaces
- the transition is legible through dependency-specific fields, not just an undifferentiated green status
- `last_failure_at` and `last_recovery_at` provide bounded post-incident context when available
- the request-serving behavior matches the new health state
- the same truth is inspectable from the existing console surfaces without inventing a new API or dashboard

A restarted dependency alone is not enough. Reachability without truthful product evidence is not recovery proof.

## What this walkthrough intentionally does not add

This document intentionally does not add:

- a new resilience dashboard
- a recovery-specific API family
- hosted-authoritative outage or recovery claims
- hidden manual database repair steps as part of the canonical proof
- a broader chaos-engineering or incident-management workflow
- duplicate contracts for fields already defined by the existing runtime and console seams

If one of those capabilities is needed later, it should be proposed explicitly in a future milestone rather than implied here.

## Failure modes this recovery proof makes obvious

These are the review shortcuts that reveal drift quickly:

- `/health/ready` claims healthy serving while a serving-critical dependency still reports `not_ready` or `recovering`
- `/health/dependencies` stops exposing dependency class, lifecycle state, serving effect, or recovery timestamps needed to explain the incident
- governance-store outage no longer fails closed on the request path
- semantic-cache outage starts blocking unrelated healthy serving paths
- `recovering` appears without corresponding serving behavior or without a later transition to `ready`
- `last_failure_at` or `last_recovery_at` disappear, contradict current state, or stop helping distinguish current failure from recovered state
- Observability or runtime health cards stop showing the same recovery metadata available from the backend
- the console starts treating dependency health as a replacement for the selected-request-first evidence model
- hosted freshness, fleet posture, or other control-plane metadata is presented as authoritative recovery truth
- the walkthrough starts implying new dashboards, new resilience APIs, or broader hosted control not already shipped

## Related docs and code-backed seams

- [`docs/hosted-reinforcement-boundary.md`](hosted-reinforcement-boundary.md) — hosted trust boundary that remains subordinate to local runtime proof
- [`docs/m009-integrated-proof.md`](m009-integrated-proof.md) — pointer-first proof pattern reused here
- `src/nebula/main.py` — `/health/ready` and `/health/dependencies`
- `tests/test_phase10_outage_safety.py` — deterministic outage and recovery proofs
- `tests/test_health.py` — focused readiness and recovery-state contract coverage
- `console/src/app/(console)/observability/page.tsx` — selected-request-first operator framing
- `console/src/components/health/runtime-health-cards.tsx` — dependency lifecycle and recovery metadata rendering
- `console/src/lib/admin-api.ts` — typed dependency-health contract for the console
- [`.gsd/milestones/M010/M010-CONTEXT.md`](../.gsd/milestones/M010/M010-CONTEXT.md) — milestone intent and acceptance boundary
- [`.gsd/milestones/M010/slices/S04/S04-RESEARCH.md`](../.gsd/milestones/M010/slices/S04/S04-RESEARCH.md) — slice-specific recovery-proof rationale
