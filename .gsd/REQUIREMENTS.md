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
- Validation: S05 validated the final narrow embeddings adoption assembly by making `docs/embeddings-integrated-adoption-proof.md` discoverable from `README.md` and `docs/architecture.md` as a pointer-only walkthrough, then rerunning `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py`, `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py`, and `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings` successfully. The assembled proof keeps `docs/embeddings-adoption-contract.md` as the only detailed public contract while tying the public `POST /v1/embeddings` path to `X-Request-ID`/`X-Nebula-*` headers, `GET /v1/admin/usage/ledger?request_id=...`, and Observability corroboration without widening Nebula into parity, SDK, hosted-plane, or unrelated infrastructure work.
- Notes: Validated by the discoverability links in README.md and docs/architecture.md, the joined proof order in docs/embeddings-integrated-adoption-proof.md, passing focused embeddings pytest coverage, and repo/doc grep checks that keep the contract, migration guide, integrated walkthrough, and requirement evidence aligned.

### R014 — Hosted/control-plane surfaces grow only where they materially improve adoption and operator confidence beyond the current metadata-only support model.
- Class: integration
- Status: validated
- Description: Hosted/control-plane surfaces grow only where they materially improve adoption and operator confidence beyond the current metadata-only support model.
- Why it matters: Hosted reinforcement is useful only if it strengthens onboarding and fleet understanding without weakening the local-authority trust boundary.
- Source: user
- Primary owning slice: M004/S01
- Supporting slices: M004/S02, M004/S03, M004/S04
- Validation: M004 validated the hosted reinforcement boundary, fleet-posture UX, integrated trust walkthrough, and close-out refinements while preserving metadata-only exports and local runtime authority.
- Notes: Validated through `console/src/lib/hosted-contract.ts`, the deployments posture surfaces, `docs/hosted-reinforcement-boundary.md`, `docs/hosted-integrated-adoption-proof.md`, focused Vitest coverage, Playwright walkthroughs, and backend hosted-contract tests.

### R032 — Hosted console gives a clear fleet posture view across linked deployments without implying hosted authority.
- Class: operability
- Status: validated
- Description: Hosted console gives a clear fleet posture view across linked deployments without implying hosted authority.
- Why it matters: Operators evaluating more than one deployment need posture synthesis, not just inventory, but the summary must stay descriptive.
- Source: user
- Primary owning slice: M004/S02
- Supporting slices: M004/S03, M004/S04
- Validation: M004 added a real fleet-posture summary and mixed-state interpretation surface on the deployments page, grounded in existing metadata and bounded-action semantics.
- Notes: Validated by the shared fleet-posture derivation seam, summary/table tests, and integrated browser proof.

### R033 — Operators can quickly distinguish linked, pending, stale, offline, and blocked deployment states from the hosted console.
- Class: failure-visibility
- Status: validated
- Description: Operators can quickly distinguish linked, pending, stale, offline, and blocked deployment states from the hosted console.
- Why it matters: Hosted reinforcement fails if operators have to infer posture by opening every deployment detail view.
- Source: user
- Primary owning slice: M004/S02
- Supporting slices: M004/S03
- Validation: M004 encoded mixed-state fleet posture and bounded-action availability into page-level and row-level hosted surfaces.
- Notes: Validated by focused tests on the deployments table, summary, and remote-action card plus the hosted deployments walkthrough.

### R034 — Hosted fleet summaries stay grounded in metadata-only facts and explicitly avoid serving-time or policy authority claims.
- Class: constraint
- Status: validated
- Description: Hosted fleet summaries stay grounded in metadata-only facts and explicitly avoid serving-time or policy authority claims.
- Why it matters: Better hosted UX is harmful if it implies that hosted now certifies local runtime truth.
- Source: user
- Primary owning slice: M004/S01
- Supporting slices: M004/S02, M004/S03, M004/S04
- Validation: M004 centralized allowed descriptive claims, prohibited authority claims, and operator reading guidance into the hosted contract seam and reused that language across UI and docs.
- Notes: Validated through shared wording reuse, grep/artifact checks, and integrated proof review.

### R035 — Hosted console makes bounded hosted action availability and blocking reasons legible without implying broader remote control.
- Class: operability
- Status: validated
- Description: Hosted console makes bounded hosted action availability and blocking reasons legible without implying broader remote control.
- Why it matters: Remote actions can strengthen confidence only if their limits remain obvious.
- Source: inferred
- Primary owning slice: M004/S02
- Supporting slices: M004/S04
- Validation: M004 reused a shared bounded-action availability seam across hosted surfaces and kept the action contract visibly narrow and fail-closed.
- Notes: Validated by remote-action card tests, deployments interpretation coverage, and the trust-boundary wording.

### R036 — Hosted onboarding and linkage state become easier to interpret for multi-deployment evaluators adopting Nebula across more than one deployment.
- Class: admin/support
- Status: validated
- Description: Hosted onboarding and linkage state become easier to interpret for multi-deployment evaluators adopting Nebula across more than one deployment.
- Why it matters: Hosted reinforcement should reduce evaluator confusion during rollout and linkage, not just display metadata.
- Source: user
- Primary owning slice: M004/S02
- Supporting slices: M004/S03
- Validation: M004 added a posture-first deployments experience that surfaces mixed-fleet linkage and freshness state without forcing operators into per-row reconstruction.
- Notes: Validated by the top-of-page fleet summary and mixed-fleet integrated proof.

### R037 — Nebula provides an integrated proof showing hosted surfaces reinforce adoption and operator confidence while local runtime enforcement remains authoritative.
- Class: quality-attribute
- Status: validated
- Description: Nebula provides an integrated proof showing hosted surfaces reinforce adoption and operator confidence while local runtime enforcement remains authoritative.
- Why it matters: Hosted reinforcement needs a joined story, not isolated UI claims.
- Source: user
- Primary owning slice: M004/S03
- Supporting slices: M004/S04
- Validation: M004 delivered a canonical hosted integrated walkthrough plus browser verification that follows the public trust-boundary page into the authenticated hosted deployments posture flow.
- Notes: Validated by `docs/hosted-integrated-adoption-proof.md`, hosted Playwright specs, and backend hosted-contract verification.

### R038 — Hosted adoption reinforcement improves operator confidence through clearer status interpretation, freshness meaning, and evidence framing.
- Class: differentiator
- Status: validated
- Description: Hosted adoption reinforcement improves operator confidence through clearer status interpretation, freshness meaning, and evidence framing.
- Why it matters: The hosted plane should make Nebula easier to trust without becoming the source of truth.
- Source: inferred
- Primary owning slice: M004/S03
- Supporting slices: M004/S04
- Validation: M004 improved posture cues, freshness interpretation, and trust-boundary wording, then revalidated the assembled hosted story in close-out.
- Notes: Validated by integrated proof artifacts and passing close-out verification.

## Active

### R039 — Nebula chooses routes using explicit decision signals and outcome-aware scoring rather than prompt-length heuristics alone.
- Class: core-capability
- Status: active
- Description: Nebula chooses routes using explicit decision signals and outcome-aware scoring rather than prompt-length heuristics alone.
- Why it matters: The current router is credible as a demo, but too shallow to be the center of a v4 control-plane story.
- Source: user
- Primary owning slice: M005/S01
- Supporting slices: M005/S03
- Validation: unmapped
- Notes: Expected decision inputs include policy mode, model allowlist, provider health, budget state, historical outcome signals, and request complexity signals.

### R040 — An operator can simulate a policy or routing change against real recent Nebula traffic before applying it.
- Class: operability
- Status: active
- Description: An operator can simulate a policy or routing change against real recent Nebula traffic before applying it.
- Why it matters: Policy changes are currently explicit but largely blind; v4 should reduce fear and guesswork.
- Source: user
- Primary owning slice: M005/S02
- Supporting slices: M005/S05
- Validation: unmapped
- Notes: The simulation should reuse existing ledger evidence rather than introduce a parallel synthetic-only planning surface.

### R041 — Tenant policy can enforce hard spend guardrails with graceful downgrade behavior rather than soft budget signals only.
- Class: integration
- Status: active
- Description: Tenant policy can enforce hard spend guardrails with graceful downgrade behavior rather than soft budget signals only.
- Why it matters: Real cost control needs enforceable behavior, not only operator interpretation after the fact.
- Source: user
- Primary owning slice: M005/S03
- Supporting slices: M005/S01
- Validation: unmapped
- Notes: Hard limits should degrade or reroute requests intentionally rather than fail ambiguously whenever possible.

### R042 — Nebula gives operators recommendation-grade feedback about which policy, routing, or cache changes would most improve cost, latency, or reliability.
- Class: differentiator
- Status: active
- Description: Nebula gives operators recommendation-grade feedback about which policy, routing, or cache changes would most improve cost, latency, or reliability.
- Why it matters: Observability that only explains the past leaves too much operator work on the table.
- Source: inferred
- Primary owning slice: M005/S04
- Supporting slices: M005/S02, M005/S03
- Validation: unmapped
- Notes: Recommendations should stay grounded in existing metadata and decision logic, not opaque black-box scoring.

### R043 — Semantic cache becomes tunable and inspectable enough that operators can improve hit quality and understand cache tradeoffs per tenant.
- Class: operability
- Status: active
- Description: Semantic cache becomes tunable and inspectable enough that operators can improve hit quality and understand cache tradeoffs per tenant.
- Why it matters: Cache value is central to Nebula's savings story, but the current product exposes almost no operator control or learning loop around it.
- Source: inferred
- Primary owning slice: M005/S04
- Supporting slices: M005/S05
- Validation: unmapped
- Notes: Threshold visibility, safe invalidation, and hit-quality evidence are stronger fits than a broad cache management subsystem.

### R044 — v4 improves decision quality and operator control without turning into broad API parity, SDK sprawl, new hosted authority, or unrelated app-platform work.
- Class: constraint
- Status: active
- Description: v4 improves decision quality and operator control without turning into broad API parity, SDK sprawl, new hosted authority, or unrelated app-platform work.
- Why it matters: The strongest v4 wedge is decisioning; losing scope discipline would blur that advantage quickly.
- Source: user
- Primary owning slice: M005/S05
- Supporting slices: M005/S01, M005/S02, M005/S03, M005/S04
- Validation: unmapped
- Notes: This is the main v4 anti-sprawl guardrail.

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
| R014 | integration | validated | M004/S01 | M004/S02, M004/S03, M004/S04 | M004 validated the hosted reinforcement boundary, fleet-posture UX, integrated trust walkthrough, and close-out refinements while preserving metadata-only exports and local runtime authority. |
| R015 | anti-feature | out-of-scope | none | none | n/a |
| R016 | anti-feature | out-of-scope | none | none | n/a |
| R017 | anti-feature | out-of-scope | none | none | n/a |
| R018 | anti-feature | out-of-scope | none | none | n/a |
| R019 | anti-feature | out-of-scope | none | none | n/a |
| R020 | primary-user-loop | validated | M003/S01 | M003/S03 | M003/S01 proved a real authenticated POST /v1/embeddings path with a strict narrow contract: string or flat list-of-strings input plus model, OpenAI-style float-vector responses, direct reuse of the existing tenant/API-key auth boundary, and passing focused coverage in tests/test_embeddings_api.py, tests/test_governance_api.py -k embeddings, and tests/test_service_flows.py -k embedding including explicit blank/upstream/empty-result branches. |
| R021 | constraint | validated | M003/S02 | M003/S05 | S02 verified the canonical embeddings contract boundary with passing focused coverage in tests/test_embeddings_api.py, tests/test_governance_api.py -k embeddings, and tests/test_service_flows.py -k embedding; confirmed docs/embeddings-adoption-contract.md exists with no TODO/TBD markers and >=6 sections; and confirmed README.md plus docs/architecture.md point readers back to the canonical file instead of restating the contract. |
| R022 | core-capability | validated | M003/S03 | M003/S05 | S03 added the executable embeddings migration proof in tests/test_embeddings_reference_migration.py plus the canonical docs/embeddings-reference-migration.md guide, demonstrating that an OpenAI-style embeddings caller can switch to Nebula with minimal caller changes (base URL plus X-Nebula-API-Key via default headers, while keeping the same client.embeddings.create call shape) and correlate X-Request-ID/X-Nebula-* response headers to GET /v1/admin/usage/ledger metadata-only evidence. Close-out verification re-ran pytest tests/test_embeddings_reference_migration.py, tests/test_embeddings_api.py, tests/test_governance_api.py -k embeddings, and tests/test_embeddings_api.py -k upstream_failures successfully, plus migration-doc integrity/discoverability checks. |
| R023 | failure-visibility | validated | M003/S04 | M003/S05 | S04 proved that the same public POST /v1/embeddings request can be correlated through X-Request-ID and X-Nebula-* headers to a metadata-only usage-ledger row, then intentionally discovered and explained in Observability by filtering Route target = embeddings and inspecting persisted request/detail fields. Close-out reran /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py and /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py successfully; console source and Playwright proof files show embeddings-specific filter/detail/operator corroboration wiring, while local Vitest/Playwright execution remained partially blocked by missing console runners in this worktree. |
| R024 | constraint | validated | M003/S05 | M003/S01, M003/S02, M003/S03, M003/S04 | S05 validated the final narrow embeddings adoption assembly by making `docs/embeddings-integrated-adoption-proof.md` discoverable from `README.md` and `docs/architecture.md` as a pointer-only walkthrough, then rerunning `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_reference_migration.py`, `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_embeddings_api.py`, and `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_governance_api.py -k embeddings` successfully. The assembled proof keeps `docs/embeddings-adoption-contract.md` as the only detailed public contract while tying the public `POST /v1/embeddings` path to `X-Request-ID`/`X-Nebula-*` headers, `GET /v1/admin/usage/ledger?request_id=...`, and Observability corroboration without widening Nebula into parity, SDK, hosted-plane, or unrelated infrastructure work. |
| R025 | integration | deferred | none | none | unmapped |
| R026 | admin/support | deferred | none | none | unmapped |
| R027 | operability | deferred | none | none | unmapped |
| R028 | anti-feature | out-of-scope | none | none | n/a |
| R029 | anti-feature | out-of-scope | none | none | n/a |
| R030 | anti-feature | out-of-scope | none | none | n/a |
| R031 | anti-feature | out-of-scope | none | none | n/a |
| R032 | operability | validated | M004/S02 | M004/S03, M004/S04 | M004 added a real fleet-posture summary and mixed-state interpretation surface on the deployments page, grounded in existing metadata and bounded-action semantics. |
| R033 | failure-visibility | validated | M004/S02 | M004/S03 | M004 encoded mixed-state fleet posture and bounded-action availability into page-level and row-level hosted surfaces. |
| R034 | constraint | validated | M004/S01 | M004/S02, M004/S03, M004/S04 | M004 centralized allowed descriptive claims, prohibited authority claims, and operator reading guidance into the hosted contract seam and reused that language across UI and docs. |
| R035 | operability | validated | M004/S02 | M004/S04 | M004 reused a shared bounded-action availability seam across hosted surfaces and kept the action contract visibly narrow and fail-closed. |
| R036 | admin/support | validated | M004/S02 | M004/S03 | M004 added a posture-first deployments experience that surfaces mixed-fleet linkage and freshness state without forcing operators into per-row reconstruction. |
| R037 | quality-attribute | validated | M004/S03 | M004/S04 | M004 delivered a canonical hosted integrated walkthrough plus browser verification that follows the public trust-boundary page into the authenticated hosted deployments posture flow. |
| R038 | differentiator | validated | M004/S03 | M004/S04 | M004 improved posture cues, freshness interpretation, and trust-boundary wording, then revalidated the assembled hosted story in close-out. |
| R039 | core-capability | active | M005/S01 | M005/S03 | unmapped |
| R040 | operability | active | M005/S02 | M005/S05 | unmapped |
| R041 | integration | active | M005/S03 | M005/S01 | unmapped |
| R042 | differentiator | active | M005/S04 | M005/S02, M005/S03 | unmapped |
| R043 | operability | active | M005/S04 | M005/S05 | unmapped |
| R044 | constraint | active | M005/S05 | M005/S01, M005/S02, M005/S03, M005/S04 | unmapped |

## Coverage Summary

- Active requirements: 6
- Mapped to slices: 6
- Validated: 23 (R001, R002, R003, R004, R005, R006, R007, R008, R009, R010, R014, R020, R021, R022, R023, R024, R032, R033, R034, R035, R036, R037, R038)
- Unmapped active requirements: 0
