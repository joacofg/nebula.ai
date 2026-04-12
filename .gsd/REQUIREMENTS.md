# Requirements

This file is the explicit capability and coverage contract for the project.

Use it to track what is actively in scope, what has been validated by completed work, what is intentionally deferred, and what is explicitly out of scope.

## Active

### R056 — Tenant policy can explicitly govern evidence retention windows for persisted request evidence.
- Class: compliance/security
- Status: active
- Description: Tenant policy can explicitly govern evidence retention windows for persisted request evidence.
- Why it matters: Operators need deliberate control over how long Nebula keeps request evidence if the product is going to claim a bounded, governable evidence layer.
- Source: user
- Primary owning slice: M008/S01
- Supporting slices: M008/S03
- Validation: mapped
- Notes: The retention model must be explicit and enforced rather than hidden in implementation.

### R057 — Tenant policy can explicitly govern metadata minimization for persisted request evidence without widening into raw payload capture.
- Class: compliance/security
- Status: active
- Description: Tenant policy can explicitly govern metadata minimization for persisted request evidence without widening into raw payload capture.
- Why it matters: Governance needs to let operators suppress unnecessary evidence detail while preserving Nebula’s bounded trust story against prompt/response persistence creep.
- Source: user
- Primary owning slice: M008/S01
- Supporting slices: M008/S02
- Validation: mapped
- Notes: This milestone governs metadata richness only; raw prompt and raw response capture remain out of scope.

### R058 — Request evidence remains historically explainable after policy changes by persisting governance markers on each ledger row.
- Class: failure-visibility
- Status: active
- Description: Request evidence remains historically explainable after policy changes by persisting governance markers on each ledger row.
- Why it matters: Operators cannot trust historical request detail if the console can only show the current tenant policy and force users to infer what applied at write time.
- Source: inferred
- Primary owning slice: M008/S02
- Supporting slices: M008/S04
- Validation: mapped
- Notes: Request detail should show what governance boundary applied to the selected persisted row, not just what the tenant policy says now.

### R059 — Retention policy is enforced as real evidence deletion, not UI-only hiding.
- Class: continuity
- Status: active
- Description: Retention policy is enforced as real evidence deletion, not UI-only hiding.
- Why it matters: A visibility-only expiry model weakens the product claim that operators can deliberately bound what evidence Nebula keeps.
- Source: user
- Primary owning slice: M008/S03
- Supporting slices: none
- Validation: mapped
- Notes: The proof bar for M008 requires actual deletion behavior.

### R060 — Operators can inspect the effective evidence boundary in the policy surface and the request-detail evidence surface.
- Class: operability
- Status: active
- Description: Operators can inspect the effective evidence boundary in the policy surface and the request-detail evidence surface.
- Why it matters: Governance is only trustworthy if the configured and effective boundary are visible where operators make and inspect decisions.
- Source: user
- Primary owning slice: M008/S04
- Supporting slices: M008/S02
- Validation: mapped
- Notes: Keep the UI footprint bounded to the existing policy and request-led operator surfaces.

### R061 — Hosted export remains metadata-only by default and M008 makes any tenant-governed evidence boundary visibly consistent with that contract.
- Class: integration
- Status: active
- Description: Hosted export remains metadata-only by default and M008 makes any tenant-governed evidence boundary visibly consistent with that contract.
- Why it matters: The hosted trust boundary is one of Nebula’s strongest current product claims; governance work should strengthen it, not blur it.
- Source: user
- Primary owning slice: M008/S04
- Supporting slices: M008/S05
- Validation: mapped
- Notes: M008 should clarify the relationship between tenant evidence governance and the existing hosted allowlist contract without making hosted authoritative.

### R062 — M008 proves the full governance chain end to end: tenant policy → persistence/export behavior → operator evidence surface → hosted trust boundary.
- Class: quality-attribute
- Status: active
- Description: M008 proves the full governance chain end to end: tenant policy → persistence/export behavior → operator evidence surface → hosted trust boundary.
- Why it matters: This milestone only feels real if operators can follow one request-level proof path instead of trusting isolated backend or UI claims.
- Source: user
- Primary owning slice: M008/S05
- Supporting slices: M008/S01, M008/S02, M008/S03, M008/S04
- Validation: mapped
- Notes: Proof should remain request-led and bounded, not turn into a generic governance dashboard.

### R063 — Evidence governance improves operator trust without weakening Nebula’s request-led debugging and interpretable evidence model.
- Class: differentiator
- Status: active
- Description: Evidence governance improves operator trust without weakening Nebula’s request-led debugging and interpretable evidence model.
- Why it matters: Nebula’s value is not just that evidence exists; it is that the evidence remains legible and useful while staying under operator control.
- Source: inferred
- Primary owning slice: M008/S05
- Supporting slices: M008/S02, M008/S04
- Validation: mapped
- Notes: Minimization and retention must stay compatible with the bounded debugging story rather than collapsing it.

### R064 — M008 stays bounded to request/policy/evidence governance and does not expand into a compliance platform, analytics product, or hosted authority layer.
- Class: constraint
- Status: active
- Description: M008 stays bounded to request/policy/evidence governance and does not expand into a compliance platform, analytics product, or hosted authority layer.
- Why it matters: Scope discipline is the difference between a strong trust-boundary milestone and a diluted governance program.
- Source: user
- Primary owning slice: M008/S05
- Supporting slices: M008/S01, M008/S02, M008/S03, M008/S04
- Validation: mapped
- Notes: This is the main anti-sprawl guardrail for M008.

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
- Notes: Proven through the public adoption contract and request-correlation tests.

### R002 — The product clearly documents what the OpenAI-compatible surface covers, what it does not cover, and where Nebula-specific value begins.
- Class: constraint
- Status: validated
- Description: The product clearly documents what the OpenAI-compatible surface covers, what it does not cover, and where Nebula-specific value begins.
- Why it matters: Fuzzy compatibility creates migration risk, support burden, and product distrust.
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: M001/S02
- Validation: validated
- Notes: Canonical contract docs and aligned discoverability links are in place.

### R003 — A developer can complete the documented happy-path integration in under 30 minutes.
- Class: launchability
- Status: validated
- Description: A developer can complete the documented happy-path integration in under 30 minutes.
- Why it matters: The milestone is about adoption speed, not just architecture clarity.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M001/S01, M001/S03, M001/S05
- Validation: validated
- Notes: Integrated adoption proof and focused runtime/UI coverage are already assembled.

### R004 — At least one realistic application or service proves direct provider usage can be replaced with Nebula with minimal code changes.
- Class: core-capability
- Status: validated
- Description: At least one realistic application or service proves direct provider usage can be replaced with Nebula with minimal code changes.
- Why it matters: A real migration story is stronger than a toy demo or abstract guidance.
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: M001/S05
- Validation: validated
- Notes: Reference migration proof is executable and correlates request headers to persisted evidence.

### R005 — The adoption experience makes routing, policy, observability, and provider abstraction visibly valuable immediately after integration.
- Class: differentiator
- Status: validated
- Description: The adoption experience makes routing, policy, observability, and provider abstraction visibly valuable immediately after integration.
- Why it matters: A pure compatibility layer lowers friction but undersells Nebula.
- Source: user
- Primary owning slice: M001/S04
- Supporting slices: M001/S03, M001/S05
- Validation: validated
- Notes: Public-request to operator-proof story already exists.

### R006 — Nebula explains tenant, app, workload, and operator boundaries clearly enough that teams know how to structure production usage.
- Class: operability
- Status: validated
- Description: Nebula explains tenant, app, workload, and operator boundaries clearly enough that teams know how to structure production usage.
- Why it matters: Adoption breaks down if teams cannot map Nebula concepts to real environments and traffic.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M002/S01
- Validation: validated
- Notes: Runtime-truth production model and console wording are aligned.

### R007 — Documentation explains adoption paths for startup product teams, platform teams, and enterprise/self-hosted operators.
- Class: admin/support
- Status: validated
- Description: Documentation explains adoption paths for startup product teams, platform teams, and enterprise/self-hosted operators.
- Why it matters: Different buyers and implementers need different framing to understand how Nebula fits.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M001/S04
- Validation: validated
- Notes: Canonical quickstart, production model, and contract docs are already in place.

### R008 — The reference integration is realistic enough that engineers trust it as a migration example rather than dismissing it as a toy.
- Class: quality-attribute
- Status: validated
- Description: The reference integration is realistic enough that engineers trust it as a migration example rather than dismissing it as a toy.
- Why it matters: Weak sample quality can undermine the whole adoption story.
- Source: inferred
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: validated
- Notes: Migration proof is grounded in real public contract changes and evidence correlation.

### R009 — A developer adopting Nebula can see what route was taken, whether fallback happened, and what policy outcome applied during integration and validation.
- Class: failure-visibility
- Status: validated
- Description: A developer adopting Nebula can see what route was taken, whether fallback happened, and what policy outcome applied during integration and validation.
- Why it matters: Early trust depends on being able to explain what happened when results differ from direct provider behavior.
- Source: inferred
- Primary owning slice: M001/S04
- Supporting slices: M001/S05
- Validation: validated
- Notes: Request explanation path is already present across headers, ledger, Playground, and Observability.

### R010 — Unsupported or deferred adoption-surface features are named explicitly so teams do not assume compatibility that Nebula does not intend to provide yet.
- Class: constraint
- Status: validated
- Description: Unsupported or deferred adoption-surface features are named explicitly so teams do not assume compatibility that Nebula does not intend to provide yet.
- Why it matters: Honest omissions reduce production surprises and wasted evaluation effort.
- Source: research
- Primary owning slice: M001/S01
- Supporting slices: none
- Validation: validated
- Notes: Unsupported/deferred boundaries are called out in canonical contract docs.

### R014 — Hosted/control-plane surfaces grow only where they materially improve adoption and operator confidence beyond the current metadata-only support model.
- Class: integration
- Status: validated
- Description: Hosted/control-plane surfaces grow only where they materially improve adoption and operator confidence beyond the current metadata-only support model.
- Why it matters: Hosted reinforcement is useful only if it strengthens onboarding and fleet understanding without weakening the local-authority trust boundary.
- Source: user
- Primary owning slice: M004/S01
- Supporting slices: M004/S02, M004/S03, M004/S04
- Validation: validated
- Notes: Hosted reinforcement already stays inside a metadata-only default export contract.

### R039 — Nebula chooses routes using explicit decision signals and outcome-aware scoring rather than prompt-length heuristics alone.
- Class: core-capability
- Status: validated
- Description: Nebula chooses routes using explicit decision signals and outcome-aware scoring rather than prompt-length heuristics alone.
- Why it matters: The current router is credible as a demo, but too shallow to be the center of a v4 control-plane story.
- Source: user
- Primary owning slice: M005/S01
- Supporting slices: M005/S03
- Validation: validated
- Notes: M006 completed the calibrated-routing proof and preserved interpretable request evidence.

### R040 — An operator can simulate a policy or routing change against real recent Nebula traffic before applying it.
- Class: operability
- Status: validated
- Description: An operator can simulate a policy or routing change against real recent Nebula traffic before applying it.
- Why it matters: Policy changes are currently explicit but largely blind; v4 should reduce fear and guesswork.
- Source: user
- Primary owning slice: M005/S02
- Supporting slices: M005/S05
- Validation: validated
- Notes: Preview-before-save replay loop is already live.

### R041 — Tenant policy can enforce hard spend guardrails with graceful downgrade behavior rather than soft budget signals only.
- Class: integration
- Status: validated
- Description: Tenant policy can enforce hard spend guardrails with graceful downgrade behavior rather than soft budget signals only.
- Why it matters: Real cost control needs enforceable behavior, not only operator interpretation after the fact.
- Source: user
- Primary owning slice: M005/S03
- Supporting slices: M005/S01
- Validation: validated
- Notes: Hard budget controls are real runtime policy, not advisory copy.

### R042 — Nebula gives operators recommendation-grade feedback about which policy, routing, or cache changes would most improve cost, latency, or reliability.
- Class: differentiator
- Status: validated
- Description: Nebula gives operators recommendation-grade feedback about which policy, routing, or cache changes would most improve cost, latency, or reliability.
- Why it matters: Observability that only explains the past leaves too much operator work on the table.
- Source: inferred
- Primary owning slice: M005/S04
- Supporting slices: M005/S02, M005/S03
- Validation: validated
- Notes: Recommendation bundle remains bounded and evidence-backed.

### R043 — Semantic cache becomes tunable and inspectable enough that operators can improve hit quality and understand cache tradeoffs per tenant.
- Class: operability
- Status: validated
- Description: Semantic cache becomes tunable and inspectable enough that operators can improve hit quality and understand cache tradeoffs per tenant.
- Why it matters: Cache value is central to Nebula's savings story, but the current product exposes almost no operator control or learning loop around it.
- Source: inferred
- Primary owning slice: M005/S04
- Supporting slices: M005/S05
- Validation: validated
- Notes: Cache tuning already lives inside tenant policy and observability context.

### R044 — v4 improves decision quality and operator control without turning into broad API parity, SDK sprawl, new hosted authority, or unrelated app-platform work.
- Class: constraint
- Status: validated
- Description: v4 improves decision quality and operator control without turning into broad API parity, SDK sprawl, new hosted authority, or unrelated app-platform work.
- Why it matters: The strongest v4 wedge is decisioning; losing scope discipline would blur that advantage quickly.
- Source: user
- Primary owning slice: M005/S05
- Supporting slices: M005/S01, M005/S02, M005/S03, M005/S04
- Validation: validated
- Notes: Scope discipline around bounded decisioning is already proven.

### R045 — Nebula calibrates routing using recent tenant-scoped observed outcomes rather than static heuristics alone.
- Class: core-capability
- Status: validated
- Description: Nebula calibrates routing using recent tenant-scoped observed outcomes rather than static heuristics alone.
- Why it matters: Outcome-aware routing is the substantive product improvement behind M006; without it, route explainability improves but route quality does not materially evolve.
- Source: user
- Primary owning slice: M006/S02
- Supporting slices: M006/S01, M006/S03
- Validation: validated
- Notes: Calibration stays bounded and interpretable.

### R046 — Operators can inspect the calibration evidence affecting current routing behavior through existing evidence surfaces.
- Class: failure-visibility
- Status: validated
- Description: Operators can inspect the calibration evidence affecting current routing behavior through existing evidence surfaces.
- Why it matters: Outcome-aware routing only improves trust if operators can still explain what happened after the fact.
- Source: user
- Primary owning slice: M006/S04
- Supporting slices: M006/S01, M006/S02
- Validation: validated
- Notes: Existing request-detail and Observability surfaces now expose calibration evidence.

### R047 — Calibrated routing fails safe to explicit heuristic behavior when evidence is missing, stale, or low-confidence.
- Class: continuity
- Status: validated
- Description: Calibrated routing fails safe to explicit heuristic behavior when evidence is missing, stale, or low-confidence.
- Why it matters: A calibration layer that fails ambiguously would weaken both routing safety and operator trust.
- Source: user
- Primary owning slice: M006/S01
- Supporting slices: M006/S02, M006/S03, M006/S04
- Validation: validated
- Notes: Degraded-mode semantics remain deterministic and visible.

### R048 — Policy simulation replay uses the same calibration semantics as live runtime routing.
- Class: integration
- Status: validated
- Description: Policy simulation replay uses the same calibration semantics as live runtime routing.
- Why it matters: Preview loses credibility if replay and runtime tell different routing stories.
- Source: user
- Primary owning slice: M006/S03
- Supporting slices: M006/S01, M006/S02, M006/S05
- Validation: validated
- Notes: Replay parity is already part of the assembled proof.

### R049 — M006 improves routing quality without becoming a black-box optimizer, analytics product, hosted-authority expansion, or unrelated platform program.
- Class: constraint
- Status: validated
- Description: M006 improves routing quality without becoming a black-box optimizer, analytics product, hosted-authority expansion, or unrelated platform program.
- Why it matters: Nebula’s wedge is interpretable operator control; losing scope discipline would blur that advantage quickly.
- Source: user
- Primary owning slice: M006/S05
- Supporting slices: M006/S01, M006/S02, M006/S03, M006/S04
- Validation: validated
- Notes: Calibrated routing stayed pointer-only and bounded.

### R050 — Observability leads with one selected request investigation flow rather than competing equally with tenant summary, recommendation, cache, or dependency panels.
- Class: operability
- Status: validated
- Description: Observability leads with one selected request investigation flow rather than competing equally with tenant summary, recommendation, cache, or dependency panels.
- Why it matters: Operators need to know what the page is for within seconds; blended roles weaken trust and slow investigation.
- Source: user
- Primary owning slice: M007/S01
- Supporting slices: M007/S03, M007/S05
- Validation: validated
- Notes: Request-led investigation flow is now established.

### R051 — Request detail shows the persisted route, provider, fallback, calibration, and policy evidence as the authoritative record, with only restrained interpretation layered on top.
- Class: failure-visibility
- Status: validated
- Description: Request detail shows the persisted route, provider, fallback, calibration, and policy evidence as the authoritative record, with only restrained interpretation layered on top.
- Why it matters: Nebula’s operator trust depends on durable evidence staying primary rather than being overshadowed by summaries or guidance.
- Source: user
- Primary owning slice: M007/S01
- Supporting slices: M007/S03, M007/S05
- Validation: validated
- Notes: This seam is especially important for M008 because historical governance markers need to keep that same evidence-first stance.

### R052 — The policy page helps an operator compare baseline versus simulated outcomes and decide whether to save, instead of feeling like a mixed settings form plus analytics surface.
- Class: operability
- Status: validated
- Description: The policy page helps an operator compare baseline versus simulated outcomes and decide whether to save, instead of feeling like a mixed settings form plus analytics surface.
- Why it matters: Replay is only valuable if operators can convert it into an explicit decision with low ambiguity.
- Source: user
- Primary owning slice: M007/S04
- Supporting slices: M007/S02, M007/S05
- Validation: validated
- Notes: M008 should add governance controls without regressing this decision-first policy workflow.

### R053 — Recommendations, calibration posture, cache posture, and dependency health remain visibly secondary to the lead evidence for the current page.
- Class: quality-attribute
- Status: validated
- Description: Recommendations, calibration posture, cache posture, and dependency health remain visibly secondary to the lead evidence for the current page.
- Why it matters: Summary cards that compete with evidence create dashboard drift and make operator reasoning less trustworthy.
- Source: inferred
- Primary owning slice: M007/S03
- Supporting slices: M007/S04, M007/S05
- Validation: validated
- Notes: M008 should keep governance visibility bounded and subordinate to lead evidence.

## Deferred

### R065 — Nebula supports broader privacy/compliance workflows such as legal holds, audit reporting, or policy approval workflows.
- Class: admin/support
- Status: deferred
- Description: Nebula supports broader privacy/compliance workflows such as legal holds, audit reporting, or policy approval workflows.
- Why it matters: These may matter for some operators later, but they are not part of Nebula’s current request/policy/evidence wedge.
- Source: inferred
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Defer unless product evidence shows a real need beyond bounded evidence governance.

### R066 — Nebula supports configurable raw prompt or raw response capture under explicit governance policy.
- Class: compliance/security
- Status: deferred
- Description: Nebula supports configurable raw prompt or raw response capture under explicit governance policy.
- Why it matters: Some environments may want this later, but it materially widens trust, storage, and privacy scope.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: M008 explicitly avoids payload-capture expansion.

### R067 — Evidence governance expands into deployment-wide or fleet-wide policy inheritance beyond tenant-scoped controls.
- Class: operability
- Status: deferred
- Description: Evidence governance expands into deployment-wide or fleet-wide policy inheritance beyond tenant-scoped controls.
- Why it matters: This might help larger fleets later, but it would widen M008 beyond the tenant-centric governance model Nebula already uses.
- Source: inferred
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Revisit only if tenant-scoped controls prove insufficient.

## Out of Scope

### R068 — Broad RBAC or enterprise permissions redesign
- Class: anti-feature
- Status: out-of-scope
- Description: Broad RBAC or enterprise permissions redesign is not part of M008.
- Why it matters: Keeps the milestone from turning into an enterprise access-control program.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Small targeted auth checks are acceptable only if they directly support the governed evidence boundary.

### R069 — Dashboard-heavy analytics expansion around evidence governance
- Class: anti-feature
- Status: out-of-scope
- Description: Dashboard-heavy analytics expansion around evidence governance is not part of M008.
- Why it matters: Prevents governance work from reopening the page-identity and dashboard-sprawl problems that M007 just closed.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Keep evidence governance visible in existing bounded surfaces.

### R070 — Hosted control plane becomes authoritative for runtime evidence or policy enforcement
- Class: anti-feature
- Status: out-of-scope
- Description: Hosted control plane becomes authoritative for runtime evidence or policy enforcement.
- Why it matters: Protects Nebula’s strongest current trust-boundary claim.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Hosted remains descriptive and metadata-only by default.

### R071 — Raw prompt or raw response persistence expansion as part of M008
- Class: anti-feature
- Status: out-of-scope
- Description: Raw prompt or raw response persistence expansion is not part of M008.
- Why it matters: Prevents accidental payload-capture creep in a milestone that is supposed to govern metadata evidence boundaries.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Existing advisory capture flags should not silently become a persistence expansion path here.

### R072 — Generic compliance/audit platform features unrelated to Nebula’s request/policy/evidence core
- Class: anti-feature
- Status: out-of-scope
- Description: Generic compliance/audit platform features unrelated to Nebula’s request/policy/evidence core are not part of M008.
- Why it matters: Prevents scope drift into a second product line.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Keep M008 tied to request-led evidence governance and operator trust.

## Traceability

| ID | Class | Status | Primary owner | Supporting | Proof |
|---|---|---|---|---|---|
| R001 | primary-user-loop | validated | M001/S01 | M001/S02, M001/S03 | validated |
| R002 | constraint | validated | M001/S01 | M001/S02 | validated |
| R003 | launchability | validated | M001/S02 | M001/S01, M001/S03, M001/S05 | validated |
| R004 | core-capability | validated | M001/S03 | M001/S05 | validated |
| R005 | differentiator | validated | M001/S04 | M001/S03, M001/S05 | validated |
| R006 | operability | validated | M001/S02 | M002/S01 | validated |
| R007 | admin/support | validated | M001/S02 | M001/S04 | validated |
| R008 | quality-attribute | validated | M001/S03 | none | validated |
| R009 | failure-visibility | validated | M001/S04 | M001/S05 | validated |
| R010 | constraint | validated | M001/S01 | none | validated |
| R014 | integration | validated | M004/S01 | M004/S02, M004/S03, M004/S04 | validated |
| R039 | core-capability | validated | M005/S01 | M005/S03 | validated |
| R040 | operability | validated | M005/S02 | M005/S05 | validated |
| R041 | integration | validated | M005/S03 | M005/S01 | validated |
| R042 | differentiator | validated | M005/S04 | M005/S02, M005/S03 | validated |
| R043 | operability | validated | M005/S04 | M005/S05 | validated |
| R044 | constraint | validated | M005/S05 | M005/S01, M005/S02, M005/S03, M005/S04 | validated |
| R045 | core-capability | validated | M006/S02 | M006/S01, M006/S03 | validated |
| R046 | failure-visibility | validated | M006/S04 | M006/S01, M006/S02 | validated |
| R047 | continuity | validated | M006/S01 | M006/S02, M006/S03, M006/S04 | validated |
| R048 | integration | validated | M006/S03 | M006/S01, M006/S02, M006/S05 | validated |
| R049 | constraint | validated | M006/S05 | M006/S01, M006/S02, M006/S03, M006/S04 | validated |
| R050 | operability | validated | M007/S01 | M007/S03, M007/S05 | validated |
| R051 | failure-visibility | validated | M007/S01 | M007/S03, M007/S05 | validated |
| R052 | operability | validated | M007/S04 | M007/S02, M007/S05 | validated |
| R053 | quality-attribute | validated | M007/S03 | M007/S04, M007/S05 | validated |
| R056 | compliance/security | active | M008/S01 | M008/S03 | mapped |
| R057 | compliance/security | active | M008/S01 | M008/S02 | mapped |
| R058 | failure-visibility | active | M008/S02 | M008/S04 | mapped |
| R059 | continuity | active | M008/S03 | none | mapped |
| R060 | operability | active | M008/S04 | M008/S02 | mapped |
| R061 | integration | active | M008/S04 | M008/S05 | mapped |
| R062 | quality-attribute | active | M008/S05 | M008/S01, M008/S02, M008/S03, M008/S04 | mapped |
| R063 | differentiator | active | M008/S05 | M008/S02, M008/S04 | mapped |
| R064 | constraint | active | M008/S05 | M008/S01, M008/S02, M008/S03, M008/S04 | mapped |
| R065 | admin/support | deferred | none | none | unmapped |
| R066 | compliance/security | deferred | none | none | unmapped |
| R067 | operability | deferred | none | none | unmapped |
| R068 | anti-feature | out-of-scope | none | none | n/a |
| R069 | anti-feature | out-of-scope | none | none | n/a |
| R070 | anti-feature | out-of-scope | none | none | n/a |
| R071 | anti-feature | out-of-scope | none | none | n/a |
| R072 | anti-feature | out-of-scope | none | none | n/a |

## Coverage Summary

- Active requirements: 9
- Mapped to slices: 9
- Validated: 27
- Unmapped active requirements: 0
