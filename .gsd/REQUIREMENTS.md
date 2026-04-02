# Requirements

This file is the explicit capability and coverage contract for the project.

Use it to track what is actively in scope, what has been validated by completed work, what is intentionally deferred, and what is explicitly out of scope.

## Active

### R039 — Nebula chooses routes using explicit decision signals and outcome-aware scoring rather than prompt-length heuristics alone.
- Class: core-capability
- Status: active
- Description: Nebula chooses routes using explicit decision signals and outcome-aware scoring rather than prompt-length heuristics alone.
- Why it matters: The current router is credible as a demo, but too shallow to be the center of Nebula’s decisioning story.
- Source: user
- Primary owning slice: M006/S01
- Supporting slices: M006/S02, M006/S03, M006/S05
- Validation: mapped
- Notes: M005 advanced the evidence model, but the live router still depends mostly on token thresholds, coarse complexity tiers, keyword hints, and policy overrides. M006 is expected to validate this requirement through calibrated routing plus parity and proof work.

### R045 — Nebula calibrates routing using recent tenant-scoped observed outcomes rather than static heuristics alone.
- Class: core-capability
- Status: active
- Description: Nebula calibrates route choice using recent tenant-scoped observed outcomes derived from existing ledger evidence rather than static heuristics alone.
- Why it matters: Outcome-aware routing is the substantive product improvement behind M006; without it, route explainability improves but route quality does not materially evolve.
- Source: user
- Primary owning slice: M006/S02
- Supporting slices: M006/S01, M006/S03
- Validation: mapped
- Notes: Calibration must stay bounded, additive, and interpretable. It should not depend on raw prompt or response persistence.

### R046 — Operators can inspect the calibration evidence affecting current routing behavior through existing evidence surfaces.
- Class: failure-visibility
- Status: active
- Description: Operators can inspect whether routing used calibration or heuristic fallback, plus the key evidence influencing that state, through existing ledger and Observability surfaces.
- Why it matters: Outcome-aware routing only improves trust if operators can still explain what happened after the fact.
- Source: user
- Primary owning slice: M006/S04
- Supporting slices: M006/S01, M006/S02
- Validation: mapped
- Notes: M006 should extend existing request-detail / Observability surfaces, not create a new analytics dashboard.

### R047 — Calibrated routing fails safe to explicit heuristic behavior when evidence is missing, stale, or low-confidence.
- Class: continuity
- Status: active
- Description: When calibration evidence is missing, stale, disabled, or low-confidence, Nebula falls back to explicit heuristic routing and marks that degraded state clearly.
- Why it matters: A calibration layer that fails ambiguously would weaken both routing safety and operator trust.
- Source: user
- Primary owning slice: M006/S01
- Supporting slices: M006/S02, M006/S03, M006/S04
- Validation: mapped
- Notes: Degraded-mode semantics must be deterministic and visible in runtime, replay, and operator evidence.

### R048 — Policy simulation replay uses the same calibration semantics as live runtime routing.
- Class: integration
- Status: active
- Description: Policy simulation replay uses the same calibration semantics, degraded-mode rules, and route-decision vocabulary as live runtime routing.
- Why it matters: Preview loses credibility if replay and runtime tell different routing stories.
- Source: user
- Primary owning slice: M006/S03
- Supporting slices: M006/S01, M006/S02, M006/S05
- Validation: mapped
- Notes: Existing replay already reconstructs requests from persisted metadata and route signals; M006 must preserve and strengthen that parity.

### R049 — M006 improves routing quality without becoming a black-box optimizer, analytics product, hosted-authority expansion, or unrelated platform program.
- Class: constraint
- Status: active
- Description: M006 improves routing quality while preserving Nebula’s anti-sprawl posture: no black-box optimizer, no analytics-product drift, no hosted-authority expansion, no raw payload capture expansion, and no broad console redesign.
- Why it matters: Nebula’s wedge is interpretable operator control; losing scope discipline would blur that advantage quickly.
- Source: user
- Primary owning slice: M006/S05
- Supporting slices: M006/S01, M006/S02, M006/S03, M006/S04
- Validation: mapped
- Notes: This is the milestone’s main anti-drift guardrail.

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
- Notes: Validated by contract tests in tests/test_chat_completions.py, tests/test_response_headers.py, tests/test_admin_playground_api.py plus docs/adoption-api-contract.md alignment.

### R002 — The product clearly documents what the OpenAI-compatible surface covers, what it does not cover, and where Nebula-specific value begins.
- Class: constraint
- Status: validated
- Description: The product clearly documents what the OpenAI-compatible surface covers, what it does not cover, and where Nebula-specific value begins.
- Why it matters: Fuzzy compatibility creates migration risk, support burden, and product distrust.
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: M001/S02
- Validation: validated
- Notes: Validated by the canonical docs/adoption-api-contract.md and aligned README.md/docs/architecture.md references back to the single source of truth.

### R003 — A developer can complete the documented happy-path integration in under 30 minutes.
- Class: launchability
- Status: validated
- Description: A developer can complete the documented happy-path integration in under 30 minutes.
- Why it matters: The milestone is about adoption speed, not just architecture clarity.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M001/S01, M001/S03, M001/S05
- Validation: validated
- Notes: Validated by the integrated adoption proof, request-correlation tests, and aligned console proof surfaces.

### R004 — At least one realistic application or service proves direct provider usage can be replaced with Nebula with minimal code changes.
- Class: core-capability
- Status: validated
- Description: At least one realistic application or service proves direct provider usage can be replaced with Nebula with minimal code changes.
- Why it matters: A real migration story is stronger than a toy demo or abstract guidance.
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: M001/S05
- Validation: validated
- Notes: Validated by tests/test_reference_migration.py plus the canonical docs/reference-migration.md guide and ledger correlation proof.

### R005 — The adoption experience makes routing, policy, observability, and provider abstraction visibly valuable immediately after integration.
- Class: differentiator
- Status: validated
- Description: The adoption experience makes routing, policy, observability, and provider abstraction visibly valuable immediately after integration.
- Why it matters: A pure compatibility layer lowers friction but undersells Nebula.
- Source: user
- Primary owning slice: M001/S04
- Supporting slices: M001/S03, M001/S05
- Validation: validated
- Notes: Validated by docs/day-1-value.md and aligned console proof surfaces around headers, ledger, Playground, and Observability.

### R006 — Nebula explains tenant, app, workload, and operator boundaries clearly enough that teams know how to structure production usage.
- Class: operability
- Status: validated
- Description: Nebula explains tenant, app, workload, and operator boundaries clearly enough that teams know how to structure production usage.
- Why it matters: Adoption breaks down if teams cannot map Nebula concepts to real environments and traffic.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M002/S01
- Validation: validated
- Notes: Validated through docs/production-model.md and focused console truth-surface coverage.

### R007 — Documentation explains adoption paths for startup product teams, platform teams, and enterprise/self-hosted operators.
- Class: admin/support
- Status: validated
- Description: Documentation explains adoption paths for startup product teams, platform teams, and enterprise/self-hosted operators.
- Why it matters: Different buyers and implementers need different framing to understand how Nebula fits.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M001/S04
- Validation: validated
- Notes: Validated by canonical quickstart, production-model, and API-contract composition.

### R008 — The reference integration is realistic enough that engineers trust it as a migration example rather than dismissing it as a toy.
- Class: quality-attribute
- Status: validated
- Description: The reference integration is realistic enough that engineers trust it as a migration example rather than dismissing it as a toy.
- Why it matters: Weak sample quality can undermine the whole adoption story.
- Source: inferred
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: validated
- Notes: Validated by the narrow before/after migration guide and focused proof tests.

### R009 — A developer adopting Nebula can see what route was taken, whether fallback happened, and what policy outcome applied during integration and validation.
- Class: failure-visibility
- Status: validated
- Description: A developer adopting Nebula can see what route was taken, whether fallback happened, and what policy outcome applied during integration and validation.
- Why it matters: Early trust depends on being able to explain what happened when results differ from direct provider behavior.
- Source: inferred
- Primary owning slice: M001/S04
- Supporting slices: M001/S05
- Validation: validated
- Notes: Validated by the request-explanation path across headers, ledger, Playground, and Observability.

### R010 — Unsupported or deferred adoption-surface features are named explicitly so teams do not assume compatibility that Nebula does not intend to provide yet.
- Class: constraint
- Status: validated
- Description: Unsupported or deferred adoption-surface features are named explicitly so teams do not assume compatibility that Nebula does not intend to provide yet.
- Why it matters: Honest omissions reduce production surprises and wasted evaluation effort.
- Source: research
- Primary owning slice: M001/S01
- Supporting slices: none
- Validation: validated
- Notes: Validated by docs/adoption-api-contract.md and the focused tests that define the current boundary.

### R014 — Hosted/control-plane surfaces grow only where they materially improve adoption and operator confidence beyond the current metadata-only support model.
- Class: integration
- Status: validated
- Description: Hosted/control-plane surfaces grow only where they materially improve adoption and operator confidence beyond the current metadata-only support model.
- Why it matters: Hosted reinforcement is useful only if it strengthens onboarding and fleet understanding without weakening the local-authority trust boundary.
- Source: user
- Primary owning slice: M004/S01
- Supporting slices: M004/S02, M004/S03, M004/S04
- Validation: validated
- Notes: Validated through hosted contract wording, deployments posture surfaces, docs, and focused verification.

### R020 — Nebula exposes a real public `/v1/embeddings` path that a common OpenAI-style embeddings caller can target without broad contract ambiguity.
- Class: primary-user-loop
- Status: validated
- Description: Nebula exposes a real public `/v1/embeddings` path that a common OpenAI-style embeddings caller can target without broad contract ambiguity.
- Why it matters: Chat-only adoption leaves a common high-demand surface uncovered.
- Source: user
- Primary owning slice: M003/S01
- Supporting slices: M003/S03
- Validation: validated
- Notes: Validated through focused embeddings runtime and governance tests.

### R021 — Nebula documents the supported embeddings boundary canonically, including what request shapes and response behavior are supported and what is intentionally out of scope.
- Class: constraint
- Status: validated
- Description: Nebula documents the supported embeddings boundary canonically, including what request shapes and response behavior are supported and what is intentionally out of scope.
- Why it matters: A narrow embeddings promise only works if adopters can see the line clearly.
- Source: user
- Primary owning slice: M003/S02
- Supporting slices: M003/S05
- Validation: validated
- Notes: Validated by docs/embeddings-adoption-contract.md plus focused route and doc integrity checks.

### R022 — Nebula proves a realistic embeddings caller can switch from a direct provider path to Nebula with minimal caller changes.
- Class: core-capability
- Status: validated
- Description: Nebula proves a realistic embeddings caller can switch from a direct provider path to Nebula with minimal caller changes.
- Why it matters: Adoption trust comes from a believable migration move, not abstract API claims.
- Source: user
- Primary owning slice: M003/S03
- Supporting slices: M003/S05
- Validation: validated
- Notes: Validated by tests/test_embeddings_reference_migration.py plus docs/embeddings-reference-migration.md and ledger correlation proof.

### R023 — The embeddings adoption path leaves enough durable evidence that a team can correlate a public request with backend/operator proof and explain the outcome.
- Class: failure-visibility
- Status: validated
- Description: The embeddings adoption path leaves enough durable evidence that a team can correlate a public request with backend/operator proof and explain the outcome.
- Why it matters: Early trust depends on being able to validate and explain the behavior.
- Source: inferred
- Primary owning slice: M003/S04
- Supporting slices: M003/S05
- Validation: validated
- Notes: Validated through shared usage-ledger and Observability corroboration for embeddings.

### R024 — The milestone widens Nebula's public adoption story without turning into broad parity work, SDK sprawl, major hosted-plane expansion, or unrelated infrastructure expansion.
- Class: constraint
- Status: validated
- Description: The milestone widens Nebula's public adoption story without turning into broad parity work, SDK sprawl, major hosted-plane expansion, or unrelated infrastructure expansion.
- Why it matters: The product value here is disciplined adoption proof.
- Source: user
- Primary owning slice: M003/S05
- Supporting slices: M003/S01, M003/S02, M003/S03, M003/S04
- Validation: validated
- Notes: Validated by the final narrow embeddings proof assembly and focused verification.

### R032 — Hosted console gives a clear fleet posture view across linked deployments without implying hosted authority.
- Class: operability
- Status: validated
- Description: Hosted console gives a clear fleet posture view across linked deployments without implying hosted authority.
- Why it matters: Operators evaluating more than one deployment need posture synthesis, not just inventory.
- Source: user
- Primary owning slice: M004/S02
- Supporting slices: M004/S03, M004/S04
- Validation: validated
- Notes: Validated by shared fleet-posture derivation, tests, and integrated browser proof.

### R033 — Operators can quickly distinguish linked, pending, stale, offline, and blocked deployment states from the hosted console.
- Class: failure-visibility
- Status: validated
- Description: Operators can quickly distinguish linked, pending, stale, offline, and blocked deployment states from the hosted console.
- Why it matters: Hosted reinforcement fails if operators have to infer posture by opening every deployment detail view.
- Source: user
- Primary owning slice: M004/S02
- Supporting slices: M004/S03
- Validation: validated
- Notes: Validated by focused table, summary, and remote-action coverage.

### R034 — Hosted fleet summaries stay grounded in metadata-only facts and explicitly avoid serving-time or policy authority claims.
- Class: constraint
- Status: validated
- Description: Hosted fleet summaries stay grounded in metadata-only facts and explicitly avoid serving-time or policy authority claims.
- Why it matters: Better hosted UX is harmful if it implies hosted now certifies local runtime truth.
- Source: user
- Primary owning slice: M004/S01
- Supporting slices: M004/S02, M004/S03, M004/S04
- Validation: validated
- Notes: Validated through shared wording reuse, artifact checks, and integrated proof review.

### R035 — Hosted console makes bounded hosted action availability and blocking reasons legible without implying broader remote control.
- Class: operability
- Status: validated
- Description: Hosted console makes bounded hosted action availability and blocking reasons legible without implying broader remote control.
- Why it matters: Remote actions can strengthen confidence only if their limits remain obvious.
- Source: inferred
- Primary owning slice: M004/S02
- Supporting slices: M004/S04
- Validation: validated
- Notes: Validated by remote-action coverage and trust-boundary wording.

### R036 — Hosted onboarding and linkage state become easier to interpret for multi-deployment evaluators adopting Nebula across more than one deployment.
- Class: admin/support
- Status: validated
- Description: Hosted onboarding and linkage state become easier to interpret for multi-deployment evaluators adopting Nebula across more than one deployment.
- Why it matters: Hosted reinforcement should reduce evaluator confusion during rollout and linkage.
- Source: user
- Primary owning slice: M004/S02
- Supporting slices: M004/S03
- Validation: validated
- Notes: Validated by the posture-first deployments experience and integrated proof.

### R037 — Nebula provides an integrated proof showing hosted surfaces reinforce adoption and operator confidence while local runtime enforcement remains authoritative.
- Class: quality-attribute
- Status: validated
- Description: Nebula provides an integrated proof showing hosted surfaces reinforce adoption and operator confidence while local runtime enforcement remains authoritative.
- Why it matters: Hosted reinforcement needs a joined story, not isolated UI claims.
- Source: user
- Primary owning slice: M004/S03
- Supporting slices: M004/S04
- Validation: validated
- Notes: Validated by docs/hosted-integrated-adoption-proof.md, browser proof, and backend verification.

### R038 — Hosted adoption reinforcement improves operator confidence through clearer status interpretation, freshness meaning, and evidence framing.
- Class: differentiator
- Status: validated
- Description: Hosted adoption reinforcement improves operator confidence through clearer status interpretation, freshness meaning, and evidence framing.
- Why it matters: The hosted plane should make Nebula easier to trust without becoming the source of truth.
- Source: inferred
- Primary owning slice: M004/S03
- Supporting slices: M004/S04
- Validation: validated
- Notes: Validated by integrated proof artifacts and close-out verification.

### R040 — An operator can simulate a policy or routing change against real recent Nebula traffic before applying it.
- Class: operability
- Status: validated
- Description: An operator can simulate a policy or routing change against real recent Nebula traffic before applying it.
- Why it matters: Policy changes are explicit but otherwise blind.
- Source: user
- Primary owning slice: M005/S02
- Supporting slices: M005/S05
- Validation: validated
- Notes: Validated by replay-only simulation, admin endpoint, and preview-before-save console UX.

### R041 — Tenant policy can enforce hard spend guardrails with graceful downgrade behavior rather than soft budget signals only.
- Class: integration
- Status: validated
- Description: Tenant policy can enforce hard spend guardrails with graceful downgrade behavior rather than soft budget signals only.
- Why it matters: Real cost control needs enforceable behavior.
- Source: user
- Primary owning slice: M005/S03
- Supporting slices: M005/S01
- Validation: validated
- Notes: Validated by hard-budget policy fields, shared runtime/simulation enforcement, and operator-visible budget evidence.

### R042 — Nebula gives operators recommendation-grade feedback about which policy, routing, or cache changes would most improve cost, latency, or reliability.
- Class: differentiator
- Status: validated
- Description: Nebula gives operators recommendation-grade feedback about which policy, routing, or cache changes would most improve cost, latency, or reliability.
- Why it matters: Observability that only explains the past leaves too much operator work on the table.
- Source: inferred
- Primary owning slice: M005/S04
- Supporting slices: M005/S02, M005/S03
- Validation: validated
- Notes: Validated by the bounded RecommendationBundle, admin endpoint, and Observability rendering.

### R043 — Semantic cache becomes tunable and inspectable enough that operators can improve hit quality and understand cache tradeoffs per tenant.
- Class: operability
- Status: validated
- Description: Semantic cache becomes tunable and inspectable enough that operators can improve hit quality and understand cache tradeoffs per tenant.
- Why it matters: Cache value is central to Nebula’s savings story.
- Source: inferred
- Primary owning slice: M005/S04
- Supporting slices: M005/S05
- Validation: validated
- Notes: Validated by explicit cache policy knobs, persistence, bounded summaries, and console coverage.

### R044 — v4 improves decision quality and operator control without turning into broad API parity, SDK sprawl, new hosted authority, or unrelated app-platform work.
- Class: constraint
- Status: validated
- Description: v4 improves decision quality and operator control without turning into broad API parity, SDK sprawl, new hosted authority, or unrelated app-platform work.
- Why it matters: The strongest v4 wedge is decisioning; losing scope discipline would blur that advantage quickly.
- Source: user
- Primary owning slice: M005/S05
- Supporting slices: M005/S01, M005/S02, M005/S03, M005/S04
- Validation: validated
- Notes: Validated by the pointer-only integrated proof plus passing focused verification.

## Deferred

### R012 — App and workload concepts become more explicit in runtime or admin product surfaces beyond documentation and conceptual guidance.
- Class: operability
- Status: deferred
- Description: App and workload concepts become more explicit in runtime or admin product surfaces beyond documentation and conceptual guidance.
- Why it matters: Larger teams may need stronger operational structure than docs alone.
- Source: inferred
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Keep deferred until Nebula needs real runtime or admin structure beyond tenant / API-key truth.

### R013 — Nebula provides dedicated helper libraries, wrappers, or SDK conveniences beyond the compatibility-first path.
- Class: admin/support
- Status: deferred
- Description: Nebula provides dedicated helper libraries, wrappers, or SDK conveniences beyond the compatibility-first path.
- Why it matters: Could reduce friction later, but broad SDK work would dilute Nebula’s focused wedge.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Explicitly avoid ecosystem expansion unless a later milestone proves it necessary.

### R050 — Operators can tune calibration sensitivity beyond a basic tenant-scoped safety toggle.
- Class: operability
- Status: deferred
- Description: Operators can tune calibration sensitivity or confidence beyond a basic tenant-scoped safety toggle.
- Why it matters: There may be future value in richer control, but adding it now would widen M006 into a tuning product.
- Source: inferred
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Keep deferred unless the narrow M006 control proves insufficient.

## Out of Scope

### R015 — Billing systems, pricing packages, and commercial packaging are not part of this planning track.
- Class: anti-feature
- Status: out-of-scope
- Description: Billing systems, pricing packages, and commercial packaging are not part of this planning track.
- Why it matters: Prevents the product from drifting into go-to-market infrastructure.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Explicit non-goal.

### R016 — A large redesign of roles, permissions, and enterprise access control is excluded.
- Class: anti-feature
- Status: out-of-scope
- Description: A large redesign of roles, permissions, and enterprise access control is excluded.
- Why it matters: Keeps Nebula from turning into an enterprise platform program.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Targeted access changes are only acceptable if they directly unblock product proof.

### R017 — Hosted-plane expansion that does not directly support adoption or operator understanding is excluded.
- Class: anti-feature
- Status: out-of-scope
- Description: Hosted-plane expansion that does not directly support adoption or operator understanding is excluded.
- Why it matters: Protects the trust boundary and keeps the product focused.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Metadata-only default export remains authoritative.

### R018 — New provider integrations or deeper orchestration work are excluded unless they directly improve routing-calibration proof.
- Class: anti-feature
- Status: out-of-scope
- Description: New provider integrations or deeper orchestration work are excluded unless they directly improve routing-calibration proof.
- Why it matters: Stops M006 from backsliding into infrastructure expansion.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Existing providers and orchestration are prior art, not the main deliverable.

### R019 — A large multi-language SDK push is excluded.
- Class: anti-feature
- Status: out-of-scope
- Description: A large multi-language SDK push is excluded.
- Why it matters: Prevents multiplying maintenance surfaces before the routing core is stronger.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Compatibility-first adoption remains the preferred integration path.

### R051 — Raw prompt or response persistence expansion for calibration is excluded.
- Class: anti-feature
- Status: out-of-scope
- Description: M006 does not expand raw prompt or response persistence to support routing calibration.
- Why it matters: Protects the metadata-only evidence posture and keeps calibration grounded in existing signals.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Calibration must derive from existing ledger-backed metadata.

### R052 — Black-box ML routing or autonomous policy mutation is excluded.
- Class: anti-feature
- Status: out-of-scope
- Description: M006 does not introduce black-box ML routing, self-applying optimization, or autonomous policy mutation.
- Why it matters: Nebula’s wedge is interpretable operator control, not opaque automation.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Prefer explicit additive scoring and operator-governed controls only.

### R053 — Broad analytics dashboards or a new routing studio UX are excluded.
- Class: anti-feature
- Status: out-of-scope
- Description: M006 does not introduce a broad analytics dashboard, routing studio, or parallel operator workflow.
- Why it matters: Keeps the milestone narrow and avoids UX/product sprawl.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Reuse existing Observability / ledger surfaces instead.

### R054 — New public API families for calibration control or evidence are excluded.
- Class: anti-feature
- Status: out-of-scope
- Description: M006 does not introduce new public API families for calibration control or routing evidence.
- Why it matters: Protects Nebula’s existing public compatibility boundary and keeps M006 internal/operator-focused.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: New work should stay within existing admin/runtime seams.

## Traceability

| ID | Class | Status | Primary owner | Supporting | Proof |
|---|---|---|---|---|---|
| R039 | core-capability | active | M006/S01 | M006/S02, M006/S03, M006/S05 | mapped |
| R045 | core-capability | active | M006/S02 | M006/S01, M006/S03 | mapped |
| R046 | failure-visibility | active | M006/S04 | M006/S01, M006/S02 | mapped |
| R047 | continuity | active | M006/S01 | M006/S02, M006/S03, M006/S04 | mapped |
| R048 | integration | active | M006/S03 | M006/S01, M006/S02, M006/S05 | mapped |
| R049 | constraint | active | M006/S05 | M006/S01, M006/S02, M006/S03, M006/S04 | mapped |
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
| R020 | primary-user-loop | validated | M003/S01 | M003/S03 | validated |
| R021 | constraint | validated | M003/S02 | M003/S05 | validated |
| R022 | core-capability | validated | M003/S03 | M003/S05 | validated |
| R023 | failure-visibility | validated | M003/S04 | M003/S05 | validated |
| R024 | constraint | validated | M003/S05 | M003/S01, M003/S02, M003/S03, M003/S04 | validated |
| R032 | operability | validated | M004/S02 | M004/S03, M004/S04 | validated |
| R033 | failure-visibility | validated | M004/S02 | M004/S03 | validated |
| R034 | constraint | validated | M004/S01 | M004/S02, M004/S03, M004/S04 | validated |
| R035 | operability | validated | M004/S02 | M004/S04 | validated |
| R036 | admin/support | validated | M004/S02 | M004/S03 | validated |
| R037 | quality-attribute | validated | M004/S03 | M004/S04 | validated |
| R038 | differentiator | validated | M004/S03 | M004/S04 | validated |
| R040 | operability | validated | M005/S02 | M005/S05 | validated |
| R041 | integration | validated | M005/S03 | M005/S01 | validated |
| R042 | differentiator | validated | M005/S04 | M005/S02, M005/S03 | validated |
| R043 | operability | validated | M005/S04 | M005/S05 | validated |
| R044 | constraint | validated | M005/S05 | M005/S01, M005/S02, M005/S03, M005/S04 | validated |
| R012 | operability | deferred | none | none | unmapped |
| R013 | admin/support | deferred | none | none | unmapped |
| R050 | operability | deferred | none | none | unmapped |
| R015 | anti-feature | out-of-scope | none | none | n/a |
| R016 | anti-feature | out-of-scope | none | none | n/a |
| R017 | anti-feature | out-of-scope | none | none | n/a |
| R018 | anti-feature | out-of-scope | none | none | n/a |
| R019 | anti-feature | out-of-scope | none | none | n/a |
| R051 | anti-feature | out-of-scope | none | none | n/a |
| R052 | anti-feature | out-of-scope | none | none | n/a |
| R053 | anti-feature | out-of-scope | none | none | n/a |
| R054 | anti-feature | out-of-scope | none | none | n/a |

## Coverage Summary

- Active requirements: 6
- Mapped to slices: 6
- Validated: 28
- Unmapped active requirements: 0
