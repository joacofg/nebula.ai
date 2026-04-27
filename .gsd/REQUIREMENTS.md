# Requirements

This file is the explicit capability and coverage contract for the project.

Use it to track what is actively in scope, what has been validated by completed work, what is intentionally deferred, and what is explicitly out of scope.

Guidelines:
- Keep requirements capability-oriented, not a giant feature wishlist.
- Requirements should be atomic, testable, and stated in plain language.
- Every **Active** requirement should be mapped to a slice, deferred, blocked with reason, or moved out of scope.
- Each requirement should have one accountable primary owner and may have supporting slices.
- Research may suggest requirements, but research does not silently make them binding.
- Validation means the requirement was actually proven by completed work and verification, not just discussed.

## Active

### R073 — Runtime routing uses recent tenant-scoped outcome evidence to improve local-vs-premium decisions.
- Class: core-capability
- Status: active
- Description: Nebula’s live routing decisions use bounded recent tenant-scoped outcome evidence to improve local-vs-premium choices rather than relying only on prompt-complexity heuristics.
- Why it matters: This is the central product move of M009; without it, the milestone is mostly explanation and replay work layered over the same old routing core.
- Source: user
- Primary owning slice: M009/S02
- Supporting slices: M009/S01
- Validation: mapped
- Notes: The routing model must remain bounded, additive, and interpretable.

### R074 — Policy simulation replay uses the same outcome-grounded routing semantics as live runtime.
- Class: integration
- Status: active
- Description: Policy simulation replay uses the same outcome-grounded routing evidence and scoring semantics as live runtime for the same tenant traffic class.
- Why it matters: Replay credibility is the control-plane trust anchor; if replay and runtime diverge, operators cannot trust preview behavior.
- Source: user
- Primary owning slice: M009/S03
- Supporting slices: M009/S01, M009/S02
- Validation: mapped
- Notes: Replay must remain deterministic, non-mutating, and explicit about approximation or degraded behavior.

### R075 — Persisted request evidence records the outcome-grounded factors that actually influenced the route decision.
- Class: failure-visibility
- Status: active
- Description: The usage-ledger row for a request records the actual outcome-grounded route factors that influenced the live route decision.
- Why it matters: Nebula’s operator story depends on request-level evidence remaining authoritative and reconstructible after the response is gone.
- Source: inferred
- Primary owning slice: M009/S02
- Supporting slices: M009/S04
- Validation: mapped
- Notes: Request evidence must stay primary while the row exists; this does not justify a separate analytics surface.

### R076 — Operators can inspect grounded vs thin/stale/degraded outcome-informed routing on existing request-first surfaces.
- Class: operability
- Status: active
- Description: Operators can inspect whether a selected request used grounded, thin, stale, or degraded outcome-informed routing on the existing request-first Observability and request-detail surfaces.
- Why it matters: Better routing only becomes trustworthy if operators can see the evidence state for the same request they are investigating.
- Source: user
- Primary owning slice: M009/S04
- Supporting slices: M009/S02, M009/S03
- Validation: mapped
- Notes: Keep request evidence primary and tenant summary context secondary.

### R077 — Outcome-grounded routing fails safe to explicit simpler behavior when evidence is missing, stale, thin, or inconsistent.
- Class: continuity
- Status: active
- Description: When outcome evidence is missing, stale, thin, or inconsistent, Nebula falls back to explicit simpler behavior and records that degraded state honestly.
- Why it matters: The milestone should make Nebula safer and more trustworthy, not more fragile or more magical.
- Source: inferred
- Primary owning slice: M009/S01
- Supporting slices: M009/S02, M009/S03, M009/S04
- Validation: mapped
- Notes: Failure handling should preserve service continuity and truthful operator evidence.

### R078 — M009 proves end-to-end routing improvement and replay credibility without widening Nebula into analytics, black-box optimization, or hosted authority.
- Class: constraint
- Status: active
- Description: M009 proves live routing improvement, replay credibility, and request-level evidence integrity without turning Nebula into a dashboard-heavy analytics product, a black-box optimizer, or a hosted-authoritative decision layer.
- Why it matters: This is the milestone’s anti-sprawl guardrail; the work can succeed technically while still failing product-wise if this boundary drifts.
- Source: user
- Primary owning slice: M009/S05
- Supporting slices: M009/S01, M009/S02, M009/S03, M009/S04
- Validation: mapped
- Notes: Keep the public API narrow, operator surfaces request-first, and hosted state non-authoritative.

## Validated

### R001 — A developer can point a common chat-completions-style application at Nebula through a stable inference entry path without redesigning the app first.
- Class: primary-user-loop
- Status: validated
- Description: A developer can point a common chat-completions-style application at Nebula through a stable inference entry path without redesigning the app first.
- Why it matters: Nebula adoption stays blocked if teams cannot start from a familiar integration move.
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: M001/S02, M001/S03
- Validation: validated
- Notes: Validated in prior milestones and retained as an active product truth.

### R039 — Nebula chooses routes using explicit decision signals and outcome-aware scoring rather than prompt-length heuristics alone.
- Class: core-capability
- Status: validated
- Description: Nebula chooses routes using explicit decision signals and outcome-aware scoring rather than prompt-length heuristics alone.
- Why it matters: This was the foundational decisioning requirement for v4 and M006.
- Source: user
- Primary owning slice: M005/S01
- Supporting slices: M005/S03
- Validation: validated
- Notes: M009 deepens the routing core beyond the validated calibrated-routing baseline rather than reopening the earlier requirement.

### R040 — An operator can simulate a policy or routing change against real recent Nebula traffic before applying it.
- Class: operability
- Status: validated
- Description: An operator can simulate a policy or routing change against real recent Nebula traffic before applying it.
- Why it matters: Policy changes are safer when previewed against real traffic.
- Source: user
- Primary owning slice: M005/S02
- Supporting slices: M005/S05
- Validation: validated
- Notes: M009 builds on this by increasing replay credibility through stronger outcome-grounded parity.

### R045 — Nebula calibrates routing using recent tenant-scoped observed outcomes rather than static heuristics alone.
- Class: core-capability
- Status: validated
- Description: Nebula calibrates routing using recent tenant-scoped observed outcomes rather than static heuristics alone.
- Why it matters: This established the tenant-scoped calibrated-routing baseline that M009 extends.
- Source: user
- Primary owning slice: M006/S02
- Supporting slices: M006/S01, M006/S03
- Validation: validated
- Notes: M009 should deepen the evidence model and runtime decision quality without undoing the bounded calibration posture.

### R046 — Operators can inspect the calibration evidence affecting current routing behavior through existing evidence surfaces.
- Class: failure-visibility
- Status: validated
- Description: Operators can inspect the calibration evidence affecting current routing behavior through existing evidence surfaces.
- Why it matters: Outcome-aware routing only improves trust if operators can still explain what happened after the fact.
- Source: user
- Primary owning slice: M006/S04
- Supporting slices: M006/S01, M006/S02
- Validation: validated
- Notes: M009 extends this request-level evidence seam to richer outcome-grounded factors.

### R047 — Calibrated routing fails safe to explicit heuristic behavior when evidence is missing, stale, or low-confidence.
- Class: continuity
- Status: validated
- Description: Calibrated routing fails safe to explicit heuristic behavior when evidence is missing, stale, or low-confidence.
- Why it matters: A calibration layer that fails ambiguously would weaken both routing safety and operator trust.
- Source: user
- Primary owning slice: M006/S01
- Supporting slices: M006/S02, M006/S03, M006/S04
- Validation: validated
- Notes: M009 should preserve and sharpen this fail-safe behavior as the evidence model gets richer.

### R048 — Policy simulation replay uses the same calibration semantics as live runtime routing.
- Class: integration
- Status: validated
- Description: Policy simulation replay uses the same calibration semantics as live runtime routing.
- Why it matters: Preview loses credibility if replay and runtime tell different routing stories.
- Source: user
- Primary owning slice: M006/S03
- Supporting slices: M006/S01, M006/S02, M006/S05
- Validation: validated
- Notes: M009 should preserve this parity while deepening the evidence model and score contract.

### R050 — Observability leads with one selected request investigation flow rather than competing equally with tenant summary, recommendation, cache, or dependency panels.
- Class: operability
- Status: validated
- Description: Observability leads with one selected request investigation flow rather than competing equally with tenant summary, recommendation, cache, or dependency panels.
- Why it matters: Operators need to know what the page is for within seconds; blended roles weaken trust and slow investigation.
- Source: user
- Primary owning slice: M007/S01
- Supporting slices: M007/S03, M007/S05
- Validation: validated
- Notes: M009 must preserve this hierarchy.

### R051 — Request detail shows the persisted route, provider, fallback, calibration, and policy evidence as the authoritative record, with only restrained interpretation layered on top.
- Class: failure-visibility
- Status: validated
- Description: Request detail shows the persisted route, provider, fallback, calibration, and policy evidence as the authoritative record, with only restrained interpretation layered on top.
- Why it matters: Nebula’s operator trust depends on durable evidence staying primary rather than being overshadowed by summaries or guidance.
- Source: user
- Primary owning slice: M007/S01
- Supporting slices: M007/S03, M007/S05
- Validation: validated
- Notes: M009 should extend this seam rather than widen into a second evidence surface.

## Deferred

### R079 — Nebula exposes tenant-level historical routing quality dashboards beyond request-first evidence inspection.
- Class: admin/support
- Status: deferred
- Description: Nebula exposes tenant-level historical routing quality dashboards beyond request-first evidence inspection.
- Why it matters: This could become useful later, but it widens the product into a broader analytics posture that is not part of M009.
- Source: inferred
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Defer unless product evidence later shows a real need beyond request-first investigation.

### R080 — Nebula supports adaptive or learned weight tuning for routing factors beyond explicit additive scoring.
- Class: differentiator
- Status: deferred
- Description: Nebula supports adaptive or learned weight tuning for routing factors beyond explicit additive scoring.
- Why it matters: This may eventually improve routing quality further, but it materially increases explainability and replay risk.
- Source: inferred
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Keep deferred unless a later milestone explicitly chooses a broader optimization posture.

### R081 — Hosted or fleet-level outcome evidence participates in routing or calibration decisions.
- Class: integration
- Status: deferred
- Description: Hosted or fleet-level outcome evidence participates in routing or calibration decisions.
- Why it matters: This may matter for broader fleet optimization later, but it would weaken Nebula’s current local-authority boundary if introduced casually.
- Source: inferred
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Hosted remains descriptive and metadata-only by default.

## Out of Scope

### R082 — M009 does not become a dashboard-heavy analytics product.
- Class: anti-feature
- Status: out-of-scope
- Description: M009 does not become a dashboard-heavy analytics product.
- Why it matters: Prevents the most likely form of scope drift in this codebase.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Keep request-level evidence primary and tenant summaries secondary.

### R083 — M009 does not introduce black-box or self-adjusting routing optimization.
- Class: anti-feature
- Status: out-of-scope
- Description: M009 does not introduce black-box or self-adjusting routing optimization.
- Why it matters: Protects Nebula’s operator-readable and replayable decisioning posture.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: The routing model must remain bounded, additive, and inspectable.

### R084 — M009 does not make the hosted plane authoritative for route choice, calibration, or evidence truth.
- Class: anti-feature
- Status: out-of-scope
- Description: M009 does not make the hosted plane authoritative for route choice, calibration, or evidence truth.
- Why it matters: Preserves Nebula’s strongest trust-boundary claim.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Hosted remains informational and metadata-only.

### R085 — M009 does not introduce a broad new public API surface for routing controls or outcome evidence.
- Class: anti-feature
- Status: out-of-scope
- Description: M009 does not introduce a broad new public API surface for routing controls or outcome evidence.
- Why it matters: Keeps the milestone focused on internal decision quality and operator control rather than surface-area expansion.
- Source: inferred
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Prefer extending existing runtime, admin, and request-evidence seams.

## Traceability

| ID | Class | Status | Primary owner | Supporting | Proof |
|---|---|---|---|---|---|
| R073 | core-capability | active | M009/S02 | M009/S01 | mapped |
| R074 | integration | active | M009/S03 | M009/S01, M009/S02 | mapped |
| R075 | failure-visibility | active | M009/S02 | M009/S04 | mapped |
| R076 | operability | active | M009/S04 | M009/S02, M009/S03 | mapped |
| R077 | continuity | active | M009/S01 | M009/S02, M009/S03, M009/S04 | mapped |
| R078 | constraint | active | M009/S05 | M009/S01, M009/S02, M009/S03, M009/S04 | mapped |
| R001 | primary-user-loop | validated | M001/S01 | M001/S02, M001/S03 | validated |
| R039 | core-capability | validated | M005/S01 | M005/S03 | validated |
| R040 | operability | validated | M005/S02 | M005/S05 | validated |
| R045 | core-capability | validated | M006/S02 | M006/S01, M006/S03 | validated |
| R046 | failure-visibility | validated | M006/S04 | M006/S01, M006/S02 | validated |
| R047 | continuity | validated | M006/S01 | M006/S02, M006/S03, M006/S04 | validated |
| R048 | integration | validated | M006/S03 | M006/S01, M006/S02, M006/S05 | validated |
| R050 | operability | validated | M007/S01 | M007/S03, M007/S05 | validated |
| R051 | failure-visibility | validated | M007/S01 | M007/S03, M007/S05 | validated |
| R079 | admin/support | deferred | none | none | unmapped |
| R080 | differentiator | deferred | none | none | unmapped |
| R081 | integration | deferred | none | none | unmapped |
| R082 | anti-feature | out-of-scope | none | none | n/a |
| R083 | anti-feature | out-of-scope | none | none | n/a |
| R084 | anti-feature | out-of-scope | none | none | n/a |
| R085 | anti-feature | out-of-scope | none | none | n/a |

## Coverage Summary

- Active requirements: 6
- Mapped to slices: 6
- Validated: 9
- Unmapped active requirements: 0
