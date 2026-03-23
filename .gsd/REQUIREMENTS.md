# Requirements

This file is the explicit capability and coverage contract for the project.

## Active

### R003 — A developer can complete the documented happy-path integration in under 30 minutes.
- Class: launchability
- Status: active
- Description: A developer can complete the documented happy-path integration in under 30 minutes.
- Why it matters: The milestone is about adoption speed, not just architecture clarity.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M001/S01, M001/S03
- Validation: mapped
- Notes: Proof should come from a real walkthrough, not just a claim in docs.

### R004 — At least one realistic application or service proves direct provider usage can be replaced with Nebula with minimal code changes.
- Class: core-capability
- Status: active
- Description: At least one realistic application or service proves direct provider usage can be replaced with Nebula with minimal code changes.
- Why it matters: A real migration story is stronger than a toy demo or abstract guidance.
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: M001/S05
- Validation: mapped
- Notes: The reference should feel credible to startup and platform-minded teams.

### R005 — The adoption experience makes routing, policy, observability, and provider abstraction visibly valuable immediately after integration.
- Class: differentiator
- Status: active
- Description: The adoption experience makes routing, policy, observability, and provider abstraction visibly valuable immediately after integration.
- Why it matters: A pure compatibility layer lowers friction but undersells Nebula.
- Source: user
- Primary owning slice: M001/S04
- Supporting slices: M001/S03, M001/S05
- Validation: mapped
- Notes: This is where the hybrid product stance needs to become legible.

### R006 — Nebula explains tenant, app, workload, and operator boundaries clearly enough that teams know how to structure production usage.
- Class: operability
- Status: active
- Description: Nebula explains tenant, app, workload, and operator boundaries clearly enough that teams know how to structure production usage.
- Why it matters: Adoption breaks down if teams cannot map Nebula concepts to real environments and traffic.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M002/S01
- Validation: mapped
- Notes: M001 may keep this partly conceptual rather than heavily enforced in product surfaces.

### R007 — Documentation explains adoption paths for startup product teams, platform teams, and enterprise/self-hosted operators.
- Class: admin/support
- Status: active
- Description: Documentation explains adoption paths for startup product teams, platform teams, and enterprise/self-hosted operators.
- Why it matters: Different buyers and implementers need different framing to understand how Nebula fits.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M001/S04
- Validation: mapped
- Notes: The docs should adapt framing without inventing different products.

### R008 — The reference integration is realistic enough that engineers trust it as a migration example rather than dismissing it as a toy.
- Class: quality-attribute
- Status: active
- Description: The reference integration is realistic enough that engineers trust it as a migration example rather than dismissing it as a toy.
- Why it matters: Weak sample quality can undermine the whole adoption story.
- Source: inferred
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: mapped
- Notes: Favor boring and believable over flashy.

### R009 — A developer adopting Nebula can see what route was taken, whether fallback happened, and what policy outcome applied during integration and validation.
- Class: failure-visibility
- Status: active
- Description: A developer adopting Nebula can see what route was taken, whether fallback happened, and what policy outcome applied during integration and validation.
- Why it matters: Early trust depends on being able to explain what happened when results differ from direct provider behavior.
- Source: inferred
- Primary owning slice: M001/S04
- Supporting slices: M001/S05
- Validation: mapped
- Notes: Existing `X-Nebula-*` headers and usage-ledger data are strong prior art here.

## Validated

### R001 — A developer can point a common chat-completions-style application at Nebula through a stable inference entry path without redesigning the app first.
- Class: primary-user-loop
- Status: validated
- Description: A developer can point a common chat-completions-style application at Nebula through a stable inference entry path without redesigning the app first.
- Why it matters: Nebula adoption stays blocked if teams cannot start from a familiar integration move.
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: M001/S02, M001/S03
- Validation: S01 established and verified a stable public adoption target on POST /v1/chat/completions with X-Nebula-API-Key auth, required user-message validation, streaming/non-streaming coverage, and canonical contract documentation grounded in tests.
- Notes: Validated by contract tests in tests/test_chat_completions.py, tests/test_response_headers.py, tests/test_admin_playground_api.py plus docs/adoption-api-contract.md alignment.

### R002 — The product clearly documents what the OpenAI-compatible surface covers, what it does not cover, and where Nebula-specific value begins.
- Class: constraint
- Status: validated
- Description: The product clearly documents what the OpenAI-compatible surface covers, what it does not cover, and where Nebula-specific value begins.
- Why it matters: Fuzzy compatibility creates migration risk, support burden, and product distrust.
- Source: user
- Primary owning slice: M001/S01
- Supporting slices: M001/S02
- Validation: S01 documents the supported public chat-completions boundary, explicit admin Playground non-equivalence, and links entry docs to the canonical contract without duplicating drifting details.
- Notes: Validated by the canonical docs/adoption-api-contract.md and aligned README.md/docs/architecture.md references back to the single source of truth.

### R010 — Unsupported or deferred adoption-surface features are named explicitly so teams do not assume compatibility that Nebula does not intend to provide yet.
- Class: constraint
- Status: validated
- Description: Unsupported or deferred adoption-surface features are named explicitly so teams do not assume compatibility that Nebula does not intend to provide yet.
- Why it matters: Honest omissions reduce production surprises and wasted evaluation effort.
- Source: research
- Primary owning slice: M001/S01
- Supporting slices: none
- Validation: S01 explicitly names unsupported or deferred adoption-surface claims, including bearer auth, admin Playground equivalence, streaming on Playground, and broader untested OpenAI-style features.
- Notes: Validated by the unsupported/deferred section in docs/adoption-api-contract.md and the focused tests that define the current boundary.

## Deferred

### R011 — Nebula supports a clearly documented public embeddings adoption path if ICP demand justifies it.
- Class: integration
- Status: deferred
- Description: Nebula supports a clearly documented public embeddings adoption path if ICP demand justifies it.
- Why it matters: Some teams will expect embeddings alongside chat, but it is not essential to the initial adoption proof.
- Source: inferred
- Primary owning slice: M002/S01
- Supporting slices: M003/S01
- Validation: unmapped
- Notes: There is embeddings-related code in the repo, but not yet a committed public adoption surface.

### R012 — App and workload concepts become more explicit in runtime or admin product surfaces beyond documentation and conceptual guidance.
- Class: operability
- Status: deferred
- Description: App and workload concepts become more explicit in runtime or admin product surfaces beyond documentation and conceptual guidance.
- Why it matters: Larger teams may need stronger operational structure than docs alone.
- Source: inferred
- Primary owning slice: M002/S02
- Supporting slices: none
- Validation: unmapped
- Notes: Defer unless M001 reveals this is a real blocker.

### R013 — Nebula provides dedicated helper libraries, wrappers, or SDK conveniences beyond the compatibility-first path.
- Class: admin/support
- Status: deferred
- Description: Nebula provides dedicated helper libraries, wrappers, or SDK conveniences beyond the compatibility-first path.
- Why it matters: Could reduce friction later, but broad SDK work would dilute this milestone.
- Source: user
- Primary owning slice: M003/S01
- Supporting slices: none
- Validation: unmapped
- Notes: Explicitly avoid ecosystem explosion in M001.

### R014 — Hosted/control-plane surfaces grow only where they materially improve adoption and operator confidence beyond the current metadata-only support model.
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

### R015 — Billing systems, pricing packages, and commercial packaging are not part of this planning track.
- Class: anti-feature
- Status: out-of-scope
- Description: Billing systems, pricing packages, and commercial packaging are not part of this planning track.
- Why it matters: Prevents the milestone from drifting into go-to-market infrastructure instead of product adoption.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Explicit non-goal for v3.0.

### R016 — A large redesign of roles, permissions, and enterprise access control is excluded.
- Class: anti-feature
- Status: out-of-scope
- Description: A large redesign of roles, permissions, and enterprise access control is excluded.
- Why it matters: Keeps the milestone from turning into an enterprise platform program.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Small targeted access changes are only acceptable if they directly unblock adoption proof.

### R017 — Hosted-plane expansion that does not directly support adoption or operator understanding is excluded.
- Class: anti-feature
- Status: out-of-scope
- Description: Hosted-plane expansion that does not directly support adoption or operator understanding is excluded.
- Why it matters: Protects the trust boundary and keeps the milestone focused.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Metadata-only default export remains authoritative for planning assumptions.

### R018 — New provider integrations or deeper orchestration work are excluded unless they directly improve integration DX.
- Class: anti-feature
- Status: out-of-scope
- Description: New provider integrations or deeper orchestration work are excluded unless they directly improve integration DX.
- Why it matters: Stops the milestone from backsliding into infrastructure expansion.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Existing routing/fallback capabilities are prior art, not the main deliverable.

### R019 — A large multi-language SDK push is excluded from this milestone.
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
| R001 | primary-user-loop | validated | M001/S01 | M001/S02, M001/S03 | S01 established and verified a stable public adoption target on POST /v1/chat/completions with X-Nebula-API-Key auth, required user-message validation, streaming/non-streaming coverage, and canonical contract documentation grounded in tests. |
| R002 | constraint | validated | M001/S01 | M001/S02 | S01 documents the supported public chat-completions boundary, explicit admin Playground non-equivalence, and links entry docs to the canonical contract without duplicating drifting details. |
| R003 | launchability | active | M001/S02 | M001/S01, M001/S03 | mapped |
| R004 | core-capability | active | M001/S03 | M001/S05 | mapped |
| R005 | differentiator | active | M001/S04 | M001/S03, M001/S05 | mapped |
| R006 | operability | active | M001/S02 | M002/S01 | mapped |
| R007 | admin/support | active | M001/S02 | M001/S04 | mapped |
| R008 | quality-attribute | active | M001/S03 | none | mapped |
| R009 | failure-visibility | active | M001/S04 | M001/S05 | mapped |
| R010 | constraint | validated | M001/S01 | none | S01 explicitly names unsupported or deferred adoption-surface claims, including bearer auth, admin Playground equivalence, streaming on Playground, and broader untested OpenAI-style features. |
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

- Active requirements: 7
- Mapped to slices: 7
- Validated: 3 (R001, R002, R010)
- Unmapped active requirements: 0
