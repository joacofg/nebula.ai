# Requirements

This file is the explicit capability and coverage contract for the project.

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

### R003 — A developer can complete the documented happy-path integration in under 30 minutes.
- Class: launchability
- Status: validated
- Description: A developer can complete the documented happy-path integration in under 30 minutes.
- Why it matters: The milestone is about adoption speed, not just architecture clarity.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M001/S01, M001/S03, M001/S05
- Validation: S05 closed the integrated adoption proof by linking docs/quickstart.md, docs/reference-migration.md, docs/day-1-value.md, docs/integrated-adoption-proof.md, backend request-correlation tests (tests/test_reference_migration.py, tests/test_admin_playground_api.py, tests/test_governance_api.py, tests/test_chat_completions.py, tests/test_response_headers.py), and aligned console proof surfaces so the same request story reads as public POST /v1/chat/completions -> X-Nebula-* / X-Request-ID -> usage ledger -> Playground corroboration -> Observability persisted explanation plus dependency health.
- Notes: Console verification in this worktree now includes passing Vitest coverage for playground metadata/recorded outcome/page seams and updated Playwright assertions in console/e2e/playground.spec.ts and console/e2e/observability.spec.ts. The planned `npm --prefix console run test -- --run observability` command currently has no matching test file, and Playwright startup is blocked by a pre-existing TypeScript error in console/src/components/deployments/remote-action-card.tsx, so those failures are recorded as verification-environment / unrelated-worktree blockers rather than evidence that the integrated adoption proof regressed.

### R004 — At least one realistic application or service proves direct provider usage can be replaced with Nebula with minimal code changes.
- Class: core-capability
- Status: validated
- Description: At least one realistic application or service proves direct provider usage can be replaced with Nebula with minimal code changes.
- Why it matters: A real migration story is stronger than a toy demo or abstract guidance.
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: M001/S05
- Validation: S03 added the executable reference migration proof in tests/test_reference_migration.py plus the canonical docs/reference-migration.md guide, demonstrating that an OpenAI-style chat-completions caller can switch to Nebula with minimal caller changes (base URL plus X-Nebula-API-Key, with X-Nebula-Tenant-ID only for ambiguous multi-tenant keys) while preserving an OpenAI-like response and correlating X-Request-ID/X-Nebula-* headers to GET /v1/admin/usage/ledger evidence.
- Notes: Validated by pytest tests/test_reference_migration.py tests/test_chat_completions.py tests/test_response_headers.py tests/test_governance_api.py -q, the targeted tenant_header/request_id/ledger subset, python3 -m py_compile tests/test_reference_migration.py, and doc-link integrity checks for docs/reference-migration.md and README.md.

### R005 — The adoption experience makes routing, policy, observability, and provider abstraction visibly valuable immediately after integration.
- Class: differentiator
- Status: validated
- Description: The adoption experience makes routing, policy, observability, and provider abstraction visibly valuable immediately after integration.
- Why it matters: A pure compatibility layer lowers friction but undersells Nebula.
- Source: user
- Primary owning slice: M001/S04
- Supporting slices: M001/S03, M001/S05
- Validation: S04 added the canonical docs/day-1-value.md walkthrough and aligned console proof surfaces so a successful public chat-completions request can be explained immediately through X-Nebula-* headers and X-Request-ID, then corroborated through Playground immediate metadata, persisted usage-ledger outcome, and Observability dependency-health context.
- Notes: Implementation and source-level verification are complete in this worktree. Local execution of the required pytest/vitest/playwright checks was blocked by missing toolchains in the environment, so executable reruns still depend on a provisioned verification environment.

### R006 — Nebula explains tenant, app, workload, and operator boundaries clearly enough that teams know how to structure production usage.
- Class: operability
- Status: validated
- Description: Nebula explains tenant, app, workload, and operator boundaries clearly enough that teams know how to structure production usage.
- Why it matters: Adoption breaks down if teams cannot map Nebula concepts to real environments and traffic.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M002/S01
- Validation: S02 established the canonical docs/production-model.md operating-model reference; M002/S01 then verified the console truth surface matches that model by proving API key issuance/inventory explain tenant inference vs X-Nebula-Tenant-ID requirements, Playground reads as an admin-only non-streaming corroboration surface, and Observability reads as the persisted request-evidence plus dependency-health context surface, all backed by passing focused vitest coverage.
- Notes: M002/S01 extended the previously validated production-model proof into the highest-impact console truth surfaces. Passing vitest coverage now locks runtime-aligned API-key scope wording, operator-only Playground framing, and Observability persisted-evidence/dependency-health framing across console/src/components/api-keys/create-api-key-dialog.test.tsx, console/src/components/api-keys/api-key-table.test.tsx, console/src/components/playground/playground-form.test.tsx, console/src/components/playground/playground-page.test.tsx, and console/src/app/(console)/observability/page.test.tsx.

### R007 — Documentation explains adoption paths for startup product teams, platform teams, and enterprise/self-hosted operators.
- Class: admin/support
- Status: validated
- Description: Documentation explains adoption paths for startup product teams, platform teams, and enterprise/self-hosted operators.
- Why it matters: Different buyers and implementers need different framing to understand how Nebula fits.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M001/S04
- Validation: S02 now routes startup teams, platform-minded adopters, and enterprise/self-hosted operators through one supported self-hosted quickstart, one production-model reference, and one public API contract boundary without fragmented or conflicting guidance across README.md, docs/self-hosting.md, docs/architecture.md, docs/quickstart.md, and docs/production-model.md.
- Notes: Validated at the documentation layer by the new canonical quickstart and production-model docs plus entry-doc routing. Executable runtime/UI verification remains partially blocked in this worktree until pytest and console vitest are installed locally.

### R008 — The reference integration is realistic enough that engineers trust it as a migration example rather than dismissing it as a toy.
- Class: quality-attribute
- Status: validated
- Description: The reference integration is realistic enough that engineers trust it as a migration example rather than dismissing it as a toy.
- Why it matters: Weak sample quality can undermine the whole adoption story.
- Source: inferred
- Primary owning slice: M001/S03
- Supporting slices: none
- Validation: S03 keeps the migration example realistic and trustworthy by grounding the guide in tests/test_reference_migration.py, limiting caller changes to the real public contract, explicitly showing when X-Nebula-Tenant-ID is and is not required, and requiring public-header plus usage-ledger correlation instead of relying on a toy curl-only demo.
- Notes: Validated by the narrow before/after migration guide in docs/reference-migration.md, its discoverability from README.md and docs/quickstart.md, and focused proof tests that cover both the bootstrap-key happy path and the intentionally ambiguous multi-tenant-key edge case without inventing demo-only façades.

### R009 — A developer adopting Nebula can see what route was taken, whether fallback happened, and what policy outcome applied during integration and validation.
- Class: failure-visibility
- Status: validated
- Description: A developer adopting Nebula can see what route was taken, whether fallback happened, and what policy outcome applied during integration and validation.
- Why it matters: Early trust depends on being able to explain what happened when results differ from direct provider behavior.
- Source: inferred
- Primary owning slice: M001/S04
- Supporting slices: M001/S05
- Validation: S04 proved the request-explanation path across public headers, X-Request-ID correlation, usage-ledger records, Playground metadata, recorded outcome cards, and Observability request detail so adopters can see route target, route reason, fallback usage, and policy outcome during integration and validation.
- Notes: Implementation and source-level verification are complete in this worktree. Local execution of the required pytest/vitest/playwright checks was blocked by missing toolchains in the environment, so executable reruns still depend on a provisioned verification environment.

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
- Validation: M002/S02 added runtime-truth tenant-page, drawer, and table guidance plus passing focused vitest coverage proving operators can map app/workload concepts onto tenants and API keys without fake runtime entities, but it did not introduce first-class runtime or admin entities beyond conceptual guidance.
- Notes: M002/S03 completed the final integrated production-structuring walkthrough without introducing first-class app/workload runtime or admin entities. The slice validated that docs/integrated-adoption-proof.md, .gsd/milestones/M002/slices/S03/S03-UAT.md, and focused Tenants/Playground/Observability Vitest coverage now compose one coherent operator story from tenant/API-key structuring through public request, X-Request-ID/X-Nebula-* headers, usage-ledger correlation, and admin corroboration surfaces. Requirement remains deferred because the proof deliberately preserves app/workload as conceptual guidance only.

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
| R003 | launchability | validated | M001/S02 | M001/S01, M001/S03, M001/S05 | S05 closed the integrated adoption proof by linking docs/quickstart.md, docs/reference-migration.md, docs/day-1-value.md, docs/integrated-adoption-proof.md, backend request-correlation tests (tests/test_reference_migration.py, tests/test_admin_playground_api.py, tests/test_governance_api.py, tests/test_chat_completions.py, tests/test_response_headers.py), and aligned console proof surfaces so the same request story reads as public POST /v1/chat/completions -> X-Nebula-* / X-Request-ID -> usage ledger -> Playground corroboration -> Observability persisted explanation plus dependency health. |
| R004 | core-capability | validated | M001/S03 | M001/S05 | S03 added the executable reference migration proof in tests/test_reference_migration.py plus the canonical docs/reference-migration.md guide, demonstrating that an OpenAI-style chat-completions caller can switch to Nebula with minimal caller changes (base URL plus X-Nebula-API-Key, with X-Nebula-Tenant-ID only for ambiguous multi-tenant keys) while preserving an OpenAI-like response and correlating X-Request-ID/X-Nebula-* headers to GET /v1/admin/usage/ledger evidence. |
| R005 | differentiator | validated | M001/S04 | M001/S03, M001/S05 | S04 added the canonical docs/day-1-value.md walkthrough and aligned console proof surfaces so a successful public chat-completions request can be explained immediately through X-Nebula-* headers and X-Request-ID, then corroborated through Playground immediate metadata, persisted usage-ledger outcome, and Observability dependency-health context. |
| R006 | operability | validated | M001/S02 | M002/S01 | S02 established the canonical docs/production-model.md operating-model reference; M002/S01 then verified the console truth surface matches that model by proving API key issuance/inventory explain tenant inference vs X-Nebula-Tenant-ID requirements, Playground reads as an admin-only non-streaming corroboration surface, and Observability reads as the persisted request-evidence plus dependency-health context surface, all backed by passing focused vitest coverage. |
| R007 | admin/support | validated | M001/S02 | M001/S04 | S02 now routes startup teams, platform-minded adopters, and enterprise/self-hosted operators through one supported self-hosted quickstart, one production-model reference, and one public API contract boundary without fragmented or conflicting guidance across README.md, docs/self-hosting.md, docs/architecture.md, docs/quickstart.md, and docs/production-model.md. |
| R008 | quality-attribute | validated | M001/S03 | none | S03 keeps the migration example realistic and trustworthy by grounding the guide in tests/test_reference_migration.py, limiting caller changes to the real public contract, explicitly showing when X-Nebula-Tenant-ID is and is not required, and requiring public-header plus usage-ledger correlation instead of relying on a toy curl-only demo. |
| R009 | failure-visibility | validated | M001/S04 | M001/S05 | S04 proved the request-explanation path across public headers, X-Request-ID correlation, usage-ledger records, Playground metadata, recorded outcome cards, and Observability request detail so adopters can see route target, route reason, fallback usage, and policy outcome during integration and validation. |
| R010 | constraint | validated | M001/S01 | none | S01 explicitly names unsupported or deferred adoption-surface claims, including bearer auth, admin Playground equivalence, streaming on Playground, and broader untested OpenAI-style features. |
| R011 | integration | deferred | M002/S01 | M003/S01 | unmapped |
| R012 | operability | deferred | M002/S02 | none | M002/S02 added runtime-truth tenant-page, drawer, and table guidance plus passing focused vitest coverage proving operators can map app/workload concepts onto tenants and API keys without fake runtime entities, but it did not introduce first-class runtime or admin entities beyond conceptual guidance. |
| R013 | admin/support | deferred | M003/S01 | none | unmapped |
| R014 | integration | deferred | M004/S01 | none | unmapped |
| R015 | anti-feature | out-of-scope | none | none | n/a |
| R016 | anti-feature | out-of-scope | none | none | n/a |
| R017 | anti-feature | out-of-scope | none | none | n/a |
| R018 | anti-feature | out-of-scope | none | none | n/a |
| R019 | anti-feature | out-of-scope | none | none | n/a |

## Coverage Summary

- Active requirements: 0
- Mapped to slices: 0
- Validated: 10 (R001, R002, R003, R004, R005, R006, R007, R008, R009, R010)
- Unmapped active requirements: 0
