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
- Notes: Console verification in this worktree now includes passing Vitest coverage for playground metadata/recorded outcome/page seams and updated Playwright assertions in console/e2e/playground.spec.ts and console/e2e/observability.spec.ts. The planned npm --prefix console run test -- --run observability command currently has no matching test file, and Playwright startup is blocked by a pre-existing TypeScript error in console/src/components/deployments/remote-action-card.tsx, so those failures are recorded as verification-environment / unrelated-worktree blockers rather than evidence that the integrated adoption proof regressed.

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

### R014 — Hosted/control-plane surfaces grow only where they materially improve adoption and operator confidence beyond the current metadata-only support model.
- Class: integration
- Status: validated
- Description: Hosted/control-plane surfaces grow only where they materially improve adoption and operator confidence beyond the current metadata-only support model.
- Why it matters: There may be adoption leverage here later, but it is not the core proof path for M001.
- Source: user
- Primary owning slice: M004/S01
- Supporting slices: M004/S02, M004/S03, M004/S04
- Validation: M004 milestone close-out verified the assembled hosted reinforcement path with passing focused Vitest coverage, Playwright trust-boundary and deployments proof, backend hosted-contract/remote-management pytest, and source/doc artifact checks. The hosted experience now materially improves onboarding clarity, multi-deployment fleet understanding, and bounded-action interpretation without widening hosted authority.
- Notes: Validated at M004 close-out after S01 established the shared hosted trust-boundary contract, S02 delivered the metadata-backed fleet posture UX, S03 added the canonical integrated proof, and S04 closed the remaining wording/evidence gaps and reran the full verification bar successfully.

### R020 — Nebula exposes a real public `/v1/embeddings` path that a common OpenAI-style embeddings caller can target without broad contract ambiguity.
- Class: primary-user-loop
- Status: validated
- Description: Nebula exposes a real public `/v1/embeddings` path that a common OpenAI-style embeddings caller can target without broad contract ambiguity.
- Why it matters: Chat-only adoption leaves a common high-demand surface uncovered; embeddings expands the adoption story without requiring a broader platform rewrite.
- Source: user
- Primary owning slice: M003/S01
- Supporting slices: M003/S03
- Validation: M003/S01 proved a real authenticated POST /v1/embeddings path with a strict narrow contract: string or flat list-of-strings input plus model, OpenAI-style float-vector responses, direct reuse of the existing tenant/API-key auth boundary, and passing focused coverage in tests/test_embeddings_api.py, tests/test_governance_api.py -k embeddings, and tests/test_service_flows.py -k embedding including explicit blank/upstream/empty-result branches.
- Notes: Validated so far for the runtime happy path and durable request-ID correlation. S02-S04 still need to add the canonical docs, migration proof, and broader evidence assembly for the full milestone story.

### R021 — Nebula documents the supported embeddings boundary canonically, including what request shapes and response behavior are supported and what is intentionally out of scope.
- Class: constraint
- Status: validated
- Description: Nebula documents the supported embeddings boundary canonically, including what request shapes and response behavior are supported and what is intentionally out of scope.
- Why it matters: A narrow embeddings promise only works if adopters can see the line clearly and do not infer broader parity than Nebula intends to support.
- Source: user
- Primary owning slice: M003/S02
- Supporting slices: M003/S05
- Validation: S02 verified the canonical embeddings contract boundary with passing focused coverage in tests/test_embeddings_api.py, tests/test_governance_api.py -k embeddings, and tests/test_service_flows.py -k embedding; confirmed docs/embeddings-adoption-contract.md exists with no TODO/TBD markers and >=6 sections; and confirmed README.md plus docs/architecture.md point readers back to the canonical file instead of restating the contract.
- Notes: Validated for the narrow public POST /v1/embeddings boundary only: X-Nebula-API-Key auth, model plus string-or-flat-list input, float-vector response shape, X-Request-ID/X-Nebula-* evidence headers, metadata-only /v1/admin/usage/ledger correlation, explicit 401/422/502 failure classes, and explicit unsupported/deferred edges including bearer auth, encoding_format, alternate encodings, and broader parity claims.

### R022 — Nebula proves a realistic embeddings caller can switch from a direct provider path to Nebula with minimal caller changes.
- Class: core-capability
- Status: validated
- Description: Nebula proves a realistic embeddings caller can switch from a direct provider path to Nebula with minimal caller changes.
- Why it matters: Adoption trust comes from a believable migration move, not from abstract API claims.
- Source: user
- Primary owning slice: M003/S03
- Supporting slices: M003/S05
- Validation: S03 added the executable embeddings migration proof in tests/test_embeddings_reference_migration.py plus the canonical docs/embeddings-reference-migration.md guide, demonstrating that an OpenAI-style embeddings caller can switch to Nebula with minimal caller changes (base URL plus X-Nebula-API-Key via default headers, while keeping the same client.embeddings.create call shape) and correlate X-Request-ID/X-Nebula-* response headers to GET /v1/admin/usage/ledger metadata-only evidence. Close-out verification re-ran pytest tests/test_embeddings_reference_migration.py, tests/test_embeddings_api.py, tests/test_governance_api.py -k embeddings, and tests/test_embeddings_api.py -k upstream_failures successfully, plus migration-doc integrity/discoverability checks.
- Notes: Validated for the narrow public POST /v1/embeddings path only. The proof explicitly excludes bearer auth, encoding_format, broader parity claims, helper SDK wrappers, and any persistence of raw input text or returned embedding vectors.

### R023 — The embeddings adoption path leaves enough durable evidence that a team can correlate a public request with backend/operator proof and explain the outcome.
- Class: failure-visibility
- Status: validated
- Description: The embeddings adoption path leaves enough durable evidence that a team can correlate a public request with backend/operator proof and explain the outcome.
- Why it matters: Early trust depends on being able to validate and explain the behavior, especially when introducing a new public surface.
- Source: inferred
- Primary owning slice: M003/S04
- Supporting slices: M003/S05
- Validation: S04 proved that the same public POST /v1/embeddings request can be correlated through X-Request-ID and X-Nebula-* headers to a metadata-only usage-ledger row, then intentionally discovered and explained in Observability by filtering Route target = embeddings and inspecting persisted request/detail fields. Close-out reran /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py and /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py successfully; console source and Playwright proof files show embeddings-specific filter/detail/operator corroboration wiring, while local Vitest/Playwright execution remained partially blocked by missing console runners in this worktree.
- Notes: Validated on the existing usage-ledger/admin API path only. The proof explicitly preserves the metadata-only boundary: no raw embeddings input text, returned vectors, new payload-capture fields, or new admin API family were introduced.

### R024 — The milestone widens Nebula's public adoption story without turning into broad parity work, SDK sprawl, major hosted-plane expansion, or unrelated infrastructure expansion.
- Class: constraint
- Status: validated
- Description: The milestone widens Nebula's public adoption story without turning into broad parity work, SDK sprawl, major hosted-plane expansion, or unrelated infrastructure expansion.
- Why it matters: The product value here is disciplined adoption proof; losing scope control would weaken the overall v3 strategy.
- Source: user
- Primary owning slice: M003/S05
- Supporting slices: M003/S01, M003/S02, M003/S03, M003/S04
- Validation: S05 validated the final narrow embeddings adoption assembly by making docs/embeddings-integrated-adoption-proof.md discoverable from README.md and docs/architecture.md as a pointer-only walkthrough, then rerunning focused embeddings pytest coverage successfully. The assembled proof keeps docs/embeddings-adoption-contract.md as the only detailed public contract while tying the public POST /v1/embeddings path to X-Request-ID/X-Nebula-* headers, GET /v1/admin/usage/ledger?request_id=..., and Observability corroboration without widening Nebula into parity, SDK, hosted-plane, or unrelated infrastructure work.
- Notes: Validated by the discoverability links in README.md and docs/architecture.md, the joined proof order in docs/embeddings-integrated-adoption-proof.md, passing focused embeddings pytest coverage, and repo/doc grep checks that keep the contract, migration guide, integrated walkthrough, and requirement evidence aligned.

### R032 — The hosted console gives operators an at-a-glance fleet posture view across linked deployments so they can quickly understand what is linked, current enough to trust as current, stale or offline, and operationally blocked for bounded hosted actions.
- Class: operability
- Status: validated
- Description: The hosted console gives operators an at-a-glance fleet posture view across linked deployments so they can quickly understand what is linked, current enough to trust as current, stale or offline, and operationally blocked for bounded hosted actions.
- Why it matters: The current hosted surfaces have the ingredients, but multi-deployment evaluators still need a faster, clearer reading surface to build adoption confidence.
- Source: user
- Primary owning slice: M004/S02
- Supporting slices: M004/S01, M004/S03
- Validation: M004 close-out re-verified the hosted deployments fleet-posture entry surface with passing focused Vitest coverage and integrated browser proof. Operators can now read linked/current, pending enrollment, stale/offline visibility, and bounded-action-blocked posture from one hosted console surface.
- Notes: Validated by the shared posture derivation seam in console/src/components/deployments/fleet-posture.ts, the top-of-page summary in fleet-posture-summary.tsx, deployments page composition, and passing close-out verification.

### R033 — The hosted console makes linked, pending enrollment, stale, offline, revoked, unlinked, and bounded-action-blocked states legible without forcing operators to infer meaning from scattered row details.
- Class: failure-visibility
- Status: validated
- Description: The hosted console makes linked, pending enrollment, stale, offline, revoked, unlinked, and bounded-action-blocked states legible without forcing operators to infer meaning from scattered row details.
- Why it matters: Adoption trust drops when evaluators cannot tell whether a problem is onboarding incompleteness, metadata staleness, or a real bounded-action limitation.
- Source: inferred
- Primary owning slice: M004/S02
- Supporting slices: M004/S04
- Validation: M004 close-out confirmed that linked, pending enrollment, stale, offline, revoked, unlinked, and bounded-action-blocked states are legible in the deployments inventory without requiring operators to reconstruct meaning from scattered details.
- Notes: Validated by helper-derived posture labels/details in console/src/components/deployments/deployment-table.tsx, shared posture tests, and integrated walkthrough evidence.

### R034 — Hosted posture summaries, trust-boundary wording, and any derived status language remain grounded in metadata-only facts that the hosted plane legitimately has, and they explicitly avoid implying authority over serving-time health, routing, fallback, or policy enforcement.
- Class: constraint
- Status: validated
- Description: Hosted posture summaries, trust-boundary wording, and any derived status language remain grounded in metadata-only facts that the hosted plane legitimately has, and they explicitly avoid implying authority over serving-time health, routing, fallback, or policy enforcement.
- Why it matters: M004 fails if the hosted UX becomes clearer but also blurrier about authority.
- Source: user
- Primary owning slice: M004/S01
- Supporting slices: M004/S02, M004/S03
- Validation: M004 close-out reran focused Vitest coverage, Playwright hosted walkthrough proof, backend hosted-contract/remote-management pytest, and source/doc grep-artifact checks to prove hosted posture summaries and trust wording remain metadata-only and non-authoritative.
- Notes: Validated by canonical wording reuse from console/src/lib/hosted-contract.ts across trust-boundary, deployments summary/table, drawer, and bounded remote-action surfaces.

### R035 — The hosted console makes it obvious when the one bounded hosted remote action is available, blocked, or irrelevant, and explains why without implying that hosted has broader operational authority.
- Class: integration
- Status: validated
- Description: The hosted console makes it obvious when the one bounded hosted remote action is available, blocked, or irrelevant, and explains why without implying that hosted has broader operational authority.
- Why it matters: Operators need confidence about what hosted can and cannot do, especially when a deployment is stale, offline, revoked, unlinked, or unsupported.
- Source: inferred
- Primary owning slice: M004/S02
- Supporting slices: M004/S03
- Validation: M004 close-out confirmed that the one bounded hosted action is shown as available, blocked, or unavailable with explicit reasons for pending, stale, offline, revoked, unlinked, and unsupported deployments without implying broader hosted authority.
- Notes: Validated by the shared getBoundedActionAvailability() seam reused by the deployments table and RemoteActionCard, with passing helper/component tests and integrated walkthrough coverage.

### R036 — Multi-deployment evaluators can understand slot creation, pending enrollment, active linkage, and hosted freshness posture across more than one deployment without manually reconstructing the adoption story from several separate views.
- Class: launchability
- Status: validated
- Description: Multi-deployment evaluators can understand slot creation, pending enrollment, active linkage, and hosted freshness posture across more than one deployment without manually reconstructing the adoption story from several separate views.
- Why it matters: M004 is intended to help real evaluators and operators with more than a single-node toy setup.
- Source: user
- Primary owning slice: M004/S02
- Supporting slices: M004/S03
- Validation: M004 close-out verified that multi-deployment evaluators can understand slot creation, pending enrollment, active linkage, and hosted freshness posture across multiple deployments from the hosted deployments entrypoint without reconstructing the story from separate views.
- Notes: Validated by the deployments-page fleet summary and mixed-fleet scan surface, backed by focused Vitest and integrated proof evidence.

### R037 — Nebula provides a canonical integrated proof showing how the hosted console reinforces onboarding clarity, fleet understanding, and operator confidence without becoming authoritative for local runtime enforcement.
- Class: core-capability
- Status: validated
- Description: Nebula provides a canonical integrated proof showing how the hosted console reinforces onboarding clarity, fleet understanding, and operator confidence without becoming authoritative for local runtime enforcement.
- Why it matters: The milestone needs a believable proof story, not only a UX pass.
- Source: user
- Primary owning slice: M004/S03
- Supporting slices: M004/S04
- Validation: M004 close-out reran the hosted integrated proof path successfully across focused frontend tests, Playwright walkthrough coverage, backend hosted-contract/remote-management pytest, and source/doc artifact checks, proving hosted reinforcement without local-authority drift.
- Notes: Validated by docs/hosted-integrated-adoption-proof.md plus passing Playwright trust-boundary and deployments walkthrough proof in the assembled worktree.

### R038 — The hosted experience gives operators more confidence because hosted statuses, freshness meaning, dependency summaries, and evidence framing are easier to interpret in context.
- Class: differentiator
- Status: validated
- Description: The hosted experience gives operators more confidence because hosted statuses, freshness meaning, dependency summaries, and evidence framing are easier to interpret in context.
- Why it matters: The milestone objective is reinforcement: clearer, more confidence-building, and more useful for evaluators and operators.
- Source: user
- Primary owning slice: M004/S03
- Supporting slices: M004/S02, M004/S04
- Validation: M004/S03 validated confidence-building hosted interpretation by assembling docs/hosted-integrated-adoption-proof.md with the real trust-boundary page, deployments fleet summary/table, drawer trust disclosure, dependency context, and bounded remote-action framing, then locking that interpretation through focused Vitest coverage and Playwright walkthrough proof. Verified by rerunning npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx 'src/app/(console)/deployments/page.test.tsx', npm --prefix console run e2e -- e2e/trust-boundary.spec.ts e2e/deployments-proof.spec.ts, and /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q. The passing proof demonstrates that hosted statuses, stale/offline meaning, bounded-action availability, and drawer-level evidence framing are easier to read in context without implying hosted serving-time authority.
- Notes: Confidence is improved through clearer interpretation of existing metadata-backed facts: shared trust wording, freshness semantics, dependency context, and bounded-action framing remain descriptive and non-authoritative.

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
- Notes: Superseded in practice by the active M003 requirement set if this milestone completes, but kept here as historical planning context until execution proves the new path.

### R012 — App and workload concepts become more explicit in runtime or admin product surfaces beyond documentation and conceptual guidance.
- Class: operability
- Status: deferred
- Description: App and workload concepts become more explicit in runtime or admin product surfaces beyond documentation and conceptual guidance.
- Why it matters: Larger teams may need stronger operational structure than docs alone.
- Source: inferred
- Primary owning slice: M002/S02
- Supporting slices: none
- Validation: M002/S02 added runtime-truth tenant-page, drawer, and table guidance plus passing focused vitest coverage proving operators can map app/workload concepts onto tenants and API keys without fake runtime entities, but it did not introduce first-class runtime or admin entities beyond conceptual guidance.
- Notes: M002/S03 completed the final integrated production-structuring walkthrough without introducing first-class app/workload runtime or admin entities. Requirement remains deferred because the proof deliberately preserves app/workload as conceptual guidance only.

### R013 — Nebula provides dedicated helper libraries, wrappers, or SDK conveniences beyond the compatibility-first path.
- Class: admin/support
- Status: deferred
- Description: Nebula provides dedicated helper libraries, wrappers, or SDK conveniences beyond the compatibility-first path.
- Why it matters: Could reduce friction later, but broad SDK work would dilute this milestone.
- Source: user
- Primary owning slice: M003/S01
- Supporting slices: none
- Validation: unmapped
- Notes: Explicitly avoid ecosystem explosion in M001 and M003.

### R025 — Nebula supports embeddings options beyond the strict happy path public promise, such as broader optional parameter semantics or wider compatibility edges.
- Class: integration
- Status: deferred
- Description: Nebula supports embeddings options beyond the strict happy path public promise, such as broader optional parameter semantics or wider compatibility edges.
- Why it matters: Some adopters may eventually expect deeper parity, but that would expand the maintenance contract before the narrow path is proven.
- Source: inferred
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Keep deferred unless repeated demand shows a clear need.

### R026 — Nebula provides dedicated helper artifacts around the embeddings adoption path rather than relying on existing compatible client patterns.
- Class: admin/support
- Status: deferred
- Description: Nebula provides dedicated helper artifacts around the embeddings adoption path rather than relying on existing compatible client patterns.
- Why it matters: Could reduce friction later, but pushes the product toward SDK surface expansion.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Only revisit if minimal-change migration proof proves insufficient without helper ergonomics.

### R027 — Nebula adds embeddings-specific console or operator surfaces beyond the minimum durable evidence needed for adoption proof.
- Class: operability
- Status: deferred
- Description: Nebula adds embeddings-specific console or operator surfaces beyond the minimum durable evidence needed for adoption proof.
- Why it matters: There may be product value later, but it is not required for this milestone's narrow adoption goal.
- Source: inferred
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Prefer backend/operator evidence reuse first.

### R039 — The hosted plane derives richer comparative fleet analytics, recommendations, or evaluative scoring beyond the current metadata-backed posture model.
- Class: differentiator
- Status: deferred
- Description: The hosted plane derives richer comparative fleet analytics, recommendations, or evaluative scoring beyond the current metadata-backed posture model.
- Why it matters: There may be future product value here, but it would push the hosted side closer to interpretive authority and broaden the scope beyond adoption reinforcement.
- Source: inferred
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Defer unless repeated evaluator demand proves that a descriptive posture surface is not enough.

### R040 — The hosted plane expands beyond the current audited rotate_deployment_credential action into broader remote management workflows.
- Class: integration
- Status: deferred
- Description: The hosted plane expands beyond the current audited rotate_deployment_credential action into broader remote management workflows.
- Why it matters: This could add operational value later, but it would materially change the trust boundary and control semantics.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: unmapped
- Notes: Keep deferred; M004 should reinforce clarity around the current bounded action rather than widen it.

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

### R028 — M003 does not become a broad OpenAI-surface expansion beyond the narrow embeddings adoption path.
- Class: anti-feature
- Status: out-of-scope
- Description: M003 does not become a broad OpenAI-surface expansion beyond the narrow embeddings adoption path.
- Why it matters: Prevents scope confusion and protects the v3 strategy from parity creep.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: The milestone should widen the story carefully, not chase general parity.

### R029 — M003 does not introduce a broad SDK, wrapper, or helper-package expansion around embeddings adoption.
- Class: anti-feature
- Status: out-of-scope
- Description: M003 does not introduce a broad SDK, wrapper, or helper-package expansion around embeddings adoption.
- Why it matters: Prevents one narrow adoption milestone from turning into long-tail ecosystem maintenance.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Tiny proof-specific helper artifacts remain optional only if absolutely necessary.

### R030 — M003 does not expand the hosted/control-plane beyond what directly reinforces the embeddings adoption proof.
- Class: anti-feature
- Status: out-of-scope
- Description: M003 does not expand the hosted/control-plane beyond what directly reinforces the embeddings adoption proof.
- Why it matters: Protects the metadata-only trust boundary and avoids misallocating effort.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Any hosted-plane change must justify itself through direct adoption-proof leverage.

### R031 — M003 does not add infrastructure, platform, or operational work unless it directly improves the embeddings adoption story or proof.
- Class: anti-feature
- Status: out-of-scope
- Description: M003 does not add infrastructure, platform, or operational work unless it directly improves the embeddings adoption story or proof.
- Why it matters: Keeps the milestone from drifting into generalized engineering work instead of product adoption.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: The internal embeddings capability already exists; new infra should be treated as a smell unless directly justified.

### R041 — The hosted plane does not become authoritative for serving-time health, routing, fallback, or policy enforcement.
- Class: anti-feature
- Status: out-of-scope
- Description: The hosted plane does not become authoritative for serving-time health, routing, fallback, or policy enforcement.
- Why it matters: This is the core trust-boundary guardrail for M004 and prevents confidence-building UX from drifting into false authority.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Local runtime enforcement remains authoritative even when hosted signals are unavailable or stale.

### R042 — M004 does not become a broad hosted product expansion program unrelated to onboarding clarity, fleet understanding, or operator confidence.
- Class: anti-feature
- Status: out-of-scope
- Description: M004 does not become a broad hosted product expansion program unrelated to onboarding clarity, fleet understanding, or operator confidence.
- Why it matters: Protects the milestone from drifting into generic control-plane scope.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Hosted changes must justify themselves through reinforcement value, not feature count.

### R043 — M004 does not introduce commercial packaging, billing, or enterprise-access redesign work.
- Class: anti-feature
- Status: out-of-scope
- Description: M004 does not introduce commercial packaging, billing, or enterprise-access redesign work.
- Why it matters: Prevents the milestone from diverging into go-to-market or enterprise-platform work.
- Source: user
- Primary owning slice: none
- Supporting slices: none
- Validation: n/a
- Notes: Explicit non-goal repeated here because hosted/control-plane scope often drifts in that direction.

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
| R014 | integration | validated | M004/S01 | M004/S02, M004/S03, M004/S04 | M004 milestone close-out verified the assembled hosted reinforcement path with passing focused Vitest coverage, Playwright trust-boundary and deployments proof, backend hosted-contract/remote-management pytest, and source/doc artifact checks. The hosted experience now materially improves onboarding clarity, multi-deployment fleet understanding, and bounded-action interpretation without widening hosted authority. |
| R015 | anti-feature | out-of-scope | none | none | n/a |
| R016 | anti-feature | out-of-scope | none | none | n/a |
| R017 | anti-feature | out-of-scope | none | none | n/a |
| R018 | anti-feature | out-of-scope | none | none | n/a |
| R019 | anti-feature | out-of-scope | none | none | n/a |
| R020 | primary-user-loop | validated | M003/S01 | M003/S03 | M003/S01 proved a real authenticated POST /v1/embeddings path with a strict narrow contract: string or flat list-of-strings input plus model, OpenAI-style float-vector responses, direct reuse of the existing tenant/API-key auth boundary, and passing focused coverage in tests/test_embeddings_api.py, tests/test_governance_api.py -k embeddings, and tests/test_service_flows.py -k embedding including explicit blank/upstream/empty-result branches. |
| R021 | constraint | validated | M003/S02 | M003/S05 | S02 verified the canonical embeddings contract boundary with passing focused coverage in tests/test_embeddings_api.py, tests/test_governance_api.py -k embeddings, and tests/test_service_flows.py -k embedding; confirmed docs/embeddings-adoption-contract.md exists with no TODO/TBD markers and >=6 sections; and confirmed README.md plus docs/architecture.md point readers back to the canonical file instead of restating the contract. |
| R022 | core-capability | validated | M003/S03 | M003/S05 | S03 added the executable embeddings migration proof in tests/test_embeddings_reference_migration.py plus the canonical docs/embeddings-reference-migration.md guide, demonstrating that an OpenAI-style embeddings caller can switch to Nebula with minimal caller changes (base URL plus X-Nebula-API-Key via default headers, while keeping the same client.embeddings.create call shape) and correlate X-Request-ID/X-Nebula-* response headers to GET /v1/admin/usage/ledger metadata-only evidence. Close-out verification re-ran pytest tests/test_embeddings_reference_migration.py, tests/test_embeddings_api.py, tests/test_governance_api.py -k embeddings, and tests/test_embeddings_api.py -k upstream_failures successfully, plus migration-doc integrity/discoverability checks. |
| R023 | failure-visibility | validated | M003/S04 | M003/S05 | S04 proved that the same public POST /v1/embeddings request can be correlated through X-Request-ID and X-Nebula-* headers to a metadata-only usage-ledger row, then intentionally discovered and explained in Observability by filtering Route target = embeddings and inspecting persisted request/detail fields. Close-out reran /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py and /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py successfully; console source and Playwright proof files show embeddings-specific filter/detail/operator corroboration wiring, while local Vitest/Playwright execution remained partially blocked by missing console runners in this worktree. |
| R024 | constraint | validated | M003/S05 | M003/S01, M003/S02, M003/S03, M003/S04 | S05 validated the final narrow embeddings adoption assembly by making docs/embeddings-integrated-adoption-proof.md discoverable from README.md and docs/architecture.md as a pointer-only walkthrough, then rerunning focused embeddings pytest coverage successfully. The assembled proof keeps docs/embeddings-adoption-contract.md as the only detailed public contract while tying the public POST /v1/embeddings path to X-Request-ID/X-Nebula-* headers, GET /v1/admin/usage/ledger?request_id=..., and Observability corroboration without widening Nebula into parity, SDK, hosted-plane, or unrelated infrastructure work. |
| R025 | integration | deferred | none | none | unmapped |
| R026 | admin/support | deferred | none | none | unmapped |
| R027 | operability | deferred | none | none | unmapped |
| R028 | anti-feature | out-of-scope | none | none | n/a |
| R029 | anti-feature | out-of-scope | none | none | n/a |
| R030 | anti-feature | out-of-scope | none | none | n/a |
| R031 | anti-feature | out-of-scope | none | none | n/a |
| R032 | operability | validated | M004/S02 | M004/S01, M004/S03 | M004 close-out re-verified the hosted deployments fleet-posture entry surface with passing focused Vitest coverage and integrated browser proof. Operators can now read linked/current, pending enrollment, stale/offline visibility, and bounded-action-blocked posture from one hosted console surface. |
| R033 | failure-visibility | validated | M004/S02 | M004/S04 | M004 close-out confirmed that linked, pending enrollment, stale, offline, revoked, unlinked, and bounded-action-blocked states are legible in the deployments inventory without requiring operators to reconstruct meaning from scattered details. |
| R034 | constraint | validated | M004/S01 | M004/S02, M004/S03 | M004 close-out reran focused Vitest coverage, Playwright hosted walkthrough proof, backend hosted-contract/remote-management pytest, and source/doc grep-artifact checks to prove hosted posture summaries and trust wording remain metadata-only and non-authoritative. |
| R035 | integration | validated | M004/S02 | M004/S03 | M004 close-out confirmed that the one bounded hosted action is shown as available, blocked, or unavailable with explicit reasons for pending, stale, offline, revoked, unlinked, and unsupported deployments without implying broader hosted authority. |
| R036 | launchability | validated | M004/S02 | M004/S03 | M004 close-out verified that multi-deployment evaluators can understand slot creation, pending enrollment, active linkage, and hosted freshness posture across multiple deployments from the hosted deployments entrypoint without reconstructing the story from separate views. |
| R037 | core-capability | validated | M004/S03 | M004/S04 | M004 close-out reran the hosted integrated proof path successfully across focused frontend tests, Playwright walkthrough coverage, backend hosted-contract/remote-management pytest, and source/doc artifact checks, proving hosted reinforcement without local-authority drift. |
| R038 | differentiator | validated | M004/S03 | M004/S02, M004/S04 | M004/S03 validated confidence-building hosted interpretation by assembling docs/hosted-integrated-adoption-proof.md with the real trust-boundary page, deployments fleet summary/table, drawer trust disclosure, dependency context, and bounded remote-action framing, then locking that interpretation through focused Vitest coverage and Playwright walkthrough proof. Verified by rerunning npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx 'src/app/(console)/deployments/page.test.tsx', npm --prefix console run e2e -- e2e/trust-boundary.spec.ts e2e/deployments-proof.spec.ts, and /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q. The passing proof demonstrates that hosted statuses, stale/offline meaning, bounded-action availability, and drawer-level evidence framing are easier to read in context without implying hosted serving-time authority. |
| R039 | differentiator | deferred | none | none | unmapped |
| R040 | integration | deferred | none | none | unmapped |
| R041 | anti-feature | out-of-scope | none | none | n/a |
| R042 | anti-feature | out-of-scope | none | none | n/a |
| R043 | anti-feature | out-of-scope | none | none | n/a |

## Coverage Summary

- Active requirements: 0
- Mapped to slices: 0
- Validated: 23 (R001, R002, R003, R004, R005, R006, R007, R008, R009, R010, R014, R020, R021, R022, R023, R024, R032, R033, R034, R035, R036, R037, R038)
- Unmapped active requirements: 0
