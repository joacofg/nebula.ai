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

### R001 — Fast adoption inference path
- Class: primary-user-loop
- Status: active
- Description: A developer can point a common chat-completions-style application at Nebula through a stable inference entry path without redesigning the app first.
- Why it matters: Nebula adoption stays blocked if teams cannot start from a familiar integration move.
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: M001/S02, M001/S03
- Validation: mapped
- Notes: The emphasis is a tight and reliable compatibility promise, not broad API coverage.

### R002 — Stable compatibility boundary
- Class: constraint
- Status: active
- Description: The product clearly documents what the OpenAI-compatible surface covers, what it does not cover, and where Nebula-specific value begins.
- Why it matters: Fuzzy compatibility creates migration risk, support burden, and product distrust.
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: M001/S02
- Validation: mapped
- Notes: Compatibility should be honest and narrow enough to stay reliable.

### R003 — Under-30-minute happy path
- Class: launchability
- Status: active
- Description: A developer can complete the documented happy-path integration in under 30 minutes.
- Why it matters: The milestone is about adoption speed, not just architecture clarity.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M001/S01, M001/S03
- Validation: mapped
- Notes: Proof should come from a real walkthrough, not just a claim in docs.

### R004 — Real migration proof
- Class: core-capability
- Status: active
- Description: At least one realistic application or service proves direct provider usage can be replaced with Nebula with minimal code changes.
- Why it matters: A real migration story is stronger than a toy demo or abstract guidance.
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: M001/S05
- Validation: mapped
- Notes: The reference should feel credible to startup and platform-minded teams.

### R005 — Day-1 operational value visibility
- Class: differentiator
- Status: active
- Description: The adoption experience makes routing, policy, observability, and provider abstraction visibly valuable immediately after integration.
- Why it matters: A pure compatibility layer lowers friction but undersells Nebula.
- Source: user
- Primary owning slice: M001/S04
- Supporting slices: M001/S03, M001/S05
- Validation: mapped
- Notes: This is where the hybrid product stance needs to become legible.

### R006 — Clear production structuring model
- Class: operability
- Status: active
- Description: Nebula explains tenant, app, workload, and operator boundaries clearly enough that teams know how to structure production usage.
- Why it matters: Adoption breaks down if teams cannot map Nebula concepts to real environments and traffic.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M002/S01
- Validation: mapped
- Notes: M001 may keep this partly conceptual rather than heavily enforced in product surfaces.

### R007 — ICP-specific adoption guidance
- Class: admin/support
- Status: active
- Description: Documentation explains adoption paths for startup product teams, platform teams, and enterprise/self-hosted operators.
- Why it matters: Different buyers and implementers need different framing to understand how Nebula fits.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M001/S04
- Validation: mapped
- Notes: The docs should adapt framing without inventing different products.

### R008 — Reference implementation credibility
- Class: quality-attribute
- Status: active
- Description: The reference integration is realistic enough that engineers trust it as a migration example rather than dismissing it as a toy.
- Why it matters: Weak sample quality can undermine the whole adoption story.
- Source: inferred
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: mapped
- Notes: Favor boring and believable over flashy.

### R009 — Failure and routing transparency during adoption
- Class: failure-visibility
- Status: active
- Description: A developer adopting Nebula can see what route was taken, whether fallback happened, and what policy outcome applied during integration and validation.
- Why it matters: Early trust depends on being able to explain what happened when results differ from direct provider behavior.
- Source: inferred
- Primary owning slice: M001/S04
- Supporting slices: M001/S05
- Validation: mapped
- Notes: Existing `X-Nebula-*` headers and usage-ledger data are strong prior art here.

### R010 — Compatibility documentation for unsupported features
- Class: constraint
- Status: active
- Description: Unsupported or deferred adoption-surface features are named explicitly so teams do not assume compatibility that Nebula does not intend to provide yet.
- Why it matters: Honest omissions reduce production surprises and wasted evaluation effort.
- Source: research
- Primary owning slice: M001/S01
- Supporting slices: none
- Validation: mapped
- Notes: This likely includes tool calling, multimodal inputs, assistants/responses, batch APIs, and broad SDK claims unless later slices add them deliberately.

## Validated

## Deferred

### R011 — Embeddings adoption surface
- Class: integration
- Status: deferred
- Description: Nebula supports a clearly documented public embeddings adoption path if ICP demand justifies it.
- Why it matters: Some teams will expect embeddings alongside chat, but it is not essential to the initial adoption proof.
- Source: inferred
- Primary owning slice: M002/S01
- Supporting slices: M003/S01
- Validation: unmapped
- Notes: There is embeddings-related code in the repo, but not yet a committed public adoption surface.

### R012 — Strong app/workload enforcement in product surfaces
- Class: operability
- Status: deferred
- Description: App and workload concepts become more explicit in runtime or admin product surfaces beyond documentation and conceptual guidance.
- Why it matters: Larger teams may need stronger operational structure than docs alone.
- Source: inferred
- Primary owning slice: M002/S02
- Supporting slices: none
- Validation: unmapped
- Notes: Defer unless M001 reveals this is a real blocker.

### R013 — Broader SDK/helper ecosystem
- Class: admin/support
- Status: deferred
- Description: Nebula provides dedicated helper libraries, wrappers, or SDK conveniences beyond the compatibility-first path.
- Why it matters: Could reduce friction later, but broad SDK work would dilute this milestone.
- Source: user
- Primary owning slice: M003/S01
- Supporting slices: none
- Validation: unmapped
- Notes: Explicitly avoid ecosystem explosion in M001.

### R014 — Hosted adoption enhancements beyond current onboarding support
- Class: integration
- Status: deferred
- Description: Hosted/control-plane surfaces grow only where they materially improve adoption and operator confidence beyond the current metadata-only support model.
- Why it matters: There may be adoption leverage here later, but it is not the core proof path for M001.
- Source: user
- Primary owning slice: M004/S01
- Supporting slices: none
- Validation: unmapped
- Notes: Must preserve the metadata-only trust boundary by default.

## Out of Scope

### R015 — Billing and commercial packaging
- Class: anti-feature
- Status: out-of-scope
- Description: Billing systems, pricing packages, and commercial packaging are not part of this planning track.
- Why it matters: Prevents the milestone from drifting into go-to-market infrastructure instead of product adoption.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Explicit non-goal for v3.0.

### R016 — Broad enterprise RBAC redesign
- Class: anti-feature
- Status: out-of-scope
- Description: A large redesign of roles, permissions, and enterprise access control is excluded.
- Why it matters: Keeps the milestone from turning into an enterprise platform program.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Small targeted access changes are only acceptable if they directly unblock adoption proof.

### R017 — Major hosted control-plane expansion unrelated to adoption
- Class: anti-feature
- Status: out-of-scope
- Description: Hosted-plane expansion that does not directly support adoption or operator understanding is excluded.
- Why it matters: Protects the trust boundary and keeps the milestone focused.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Metadata-only default export remains authoritative for planning assumptions.

### R018 — Deep new provider/orchestration work not tied to integration DX
- Class: anti-feature
- Status: out-of-scope
- Description: New provider integrations or deeper orchestration work are excluded unless they directly improve integration DX.
- Why it matters: Stops the milestone from backsliding into infrastructure expansion.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Existing routing/fallback capabilities are prior art, not the main deliverable.

### R019 — Broad multi-language SDK explosion in one milestone
- Class: anti-feature
- Status: out-of-scope
- Description: A large multi-language SDK push is excluded from this milestone.
- Why it matters: Prevents the team from multiplying maintenance surfaces before the compatibility contract is stable.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: The adoption path should work first through existing OpenAI-compatible client patterns.

## Traceability

| ID | Class | Status | Primary owner | Supporting | Proof |
|---|---|---|---|---|---|
| R001 | primary-user-loop | active | M001/S01 | M001/S02, M001/S03 | mapped |
| R002 | constraint | active | M001/S01 | M001/S02 | mapped |
| R003 | launchability | active | M001/S02 | M001/S01, M001/S03 | mapped |
| R004 | core-capability | active | M001/S03 | M001/S05 | mapped |
| R005 | differentiator | active | M001/S04 | M001/S03, M001/S05 | mapped |
| R006 | operability | active | M001/S02 | M002/S01 | mapped |
| R007 | admin/support | active | M001/S02 | M001/S04 | mapped |
| R008 | quality-attribute | active | M001/S03 | none | mapped |
| R009 | failure-visibility | active | M001/S04 | M001/S05 | mapped |
| R010 | constraint | active | M001/S01 | none | mapped |
| R011 | integration | deferred | M002/S01 | M003/S01 | unmapped |
| R012 | operability | deferred | M002/S02 | none | unmapped |
| R013 | admin/support | deferred | M003/S01 | none | unmapped |
| R014 | integration | deferred | M004/S01 | none | unmapped |
| R015 | anti-feature | out-of-scope | none | none | n/a |
| R016 | anti-feature | out-of-scope | none | none | n/a |
| R017 | anti-feature | out-of-scope | none | none | n/a |
| R018 | anti-feature | out-of-scope | none | none | n/a |
| R019 | anti-feature | out-of-scope | none | none | n/a |

## Coverage Summary

- Active requirements: 10
- Mapped to slices: 10
- Validated: 0
- Unmapped active requirements: 0
