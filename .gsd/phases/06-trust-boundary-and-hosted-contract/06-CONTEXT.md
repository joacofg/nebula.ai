# Phase 6: Trust Boundary and Hosted Contract - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Freeze the hybrid hosted/self-hosted contract before any deployment-linking work begins. This phase defines how Nebula positions the hosted control plane, what metadata can leave the customer environment by default, how hosted status language works, and where the trust boundary must be disclosed. It does not add deployment enrollment, fleet inventory, remote actions, or broader hosted account scope.

</domain>

<decisions>
## Implementation Decisions

### Hosted positioning
- The hosted control plane should be framed as the recommended operating model for pilots, while remaining optional for self-hosted customers.
- Nebula should preserve the message that a fully self-hosted deployment is still a real and complete product, not a crippled mode.
- The primary value claim for the hosted layer should be easier onboarding and clearer fleet visibility, with safer limited remote operations as a supporting benefit rather than the lead pitch.
- The product should state clearly that the hosted layer is not in the request-serving path and does not become authoritative for local runtime enforcement.

### Data export contract
- The default hosted-data posture should be minimal-by-default and metadata-only.
- Hosted-visible default fields may include deployment identity, operator-assigned labels, environment, Nebula version, capability flags, registration timestamps, last-seen/freshness timestamps, coarse dependency summary, and remote-action audit summaries.
- Hosted-visible default data must exclude raw prompts, responses, provider credentials, raw usage-ledger rows, tenant secrets, and authoritative runtime policy state.
- Richer diagnostics should be explicit and separate from the default contract. If later phases add diagnostic export or bundle upload flows, those should be operator-initiated and clearly framed as exceptions to the default boundary.

### Status language
- Hosted status must never collapse into a single generic "healthy" claim.
- The primary hosted-plane status should describe control-plane freshness using `connected`, `degraded`, `stale`, and `offline` semantics.
- Local runtime health should remain a separate, explicitly reported signal rather than being implied by hosted freshness.
- Hosted copy should prefer truthful uncertainty over optimism: timestamps, last-reported wording, and reason codes should make it clear when Nebula is showing reported local state versus current hosted connectivity.

### Disclosure surfaces
- The trust boundary should be visible in three places: linking/onboarding flow, hosted deployment detail surfaces, and canonical documentation.
- The linking flow should explain the outbound-only relationship and the default metadata contract before a deployment is connected.
- Hosted deployment detail views should include a durable "what this deployment shares" or trust-boundary disclosure surface, not just a documentation link.
- Canonical docs should carry the longer-form explanation in the architecture and self-hosting narratives so pilot evaluators can verify the boundary outside the UI.

### Claude's Discretion
- Exact field names, schema naming, and payload shape for the hosted metadata contract.
- Exact UI treatment of the trust-boundary disclosure card, banners, or callouts, as long as the boundary stays persistent and unambiguous.
- Exact wording for status reason codes and the split between top-level badge text versus supporting explanatory copy.

</decisions>

<specifics>
## Specific Ideas

- Nebula should read as "self-hosted with an optional hosted control plane" rather than "cloud product with an on-prem agent."
- The strongest hosted story is operational clarity, not cloud centralization.
- The trust boundary should become a product feature: operators should be able to inspect what leaves the environment without reading security fine print.
- Hosted freshness should read as "what the control plane last heard" rather than "the deployment is definitely healthy now."

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and milestone framing
- `.planning/PROJECT.md` — Current milestone goal, hybrid-model constraints, and the self-hosted-first product position that Phase 6 must preserve.
- `.planning/REQUIREMENTS.md` — Phase 6 requirements `TRST-01` and `TRST-02`, plus adjacent milestone boundaries that must not expand here.
- `.planning/ROADMAP.md` — Phase 6 goal, success criteria, and plan breakdown.
- `.planning/STATE.md` — Current milestone state and the locked v2.0 decisions already carried forward.

### Prior decisions that constrain Phase 6
- `.planning/phases/01-self-hosted-foundation/01-CONTEXT.md` — Canonical self-hosted deployment shape, degraded-mode behavior, and the requirement that outages should remain visible instead of hidden.
- `.planning/phases/02-operator-console/02-CONTEXT.md` — Operator-console tone and the compact, precise control-plane UX direction that hosted surfaces should preserve.
- `.planning/phases/04-governance-hardening/04-CONTEXT.md` — Runtime-authoritative boundary language and the prior decision to make active control surfaces match true runtime authority.
- `.planning/phases/05-product-proof-delivery/05-CONTEXT.md` — Pilot/demo narrative principles and the benchmark-led product-proof framing that Phase 6 documentation should stay compatible with.

### Existing docs that define the current product story
- `README.md` — Current top-level product framing and operator entrypoint.
- `docs/architecture.md` — Current self-hosted architecture narrative that will need the hosted-boundary extension.
- `docs/self-hosting.md` — Canonical self-hosted deployment runbook that must remain truthful if the hosted control plane is optional.
- `docs/demo-script.md` — Existing demo narrative that later pilot proof work will extend from the Phase 6 contract.
- `docs/pilot-checklist.md` — Pilot-readiness framing that later phases will build on.

### Existing code and UI surfaces
- `.planning/codebase/ARCHITECTURE.md` — Current backend layering, FastAPI composition root, and local runtime authority.
- `.planning/codebase/STRUCTURE.md` — Repository layout and likely insertion points for hosted docs or UI surfaces.
- `.planning/codebase/CONVENTIONS.md` — Existing Python/TypeScript style and integration conventions to preserve.
- `console/src/components/shell/operator-shell.tsx` — Current operator-console shell and tone that inform hosted-surface presentation.
- `console/src/app/layout.tsx` — Existing console metadata and root layout conventions.
- `console/src/app/page.tsx` — Existing login entrypoint and first-screen pattern that informs where trust-boundary onboarding may appear.
- `console/src/app/globals.css` — Current console visual system and information-density conventions.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `docs/architecture.md`: already explains the self-hosted request path and operator-console relationship, so Phase 6 can extend a real architecture narrative instead of inventing a new one.
- `docs/self-hosting.md`: already anchors one supported self-hosted topology, making it the right place to state that hosted linking is optional and not required for serving.
- `console/src/components/shell/operator-shell.tsx`: establishes the compact, precise control-plane tone that hosted surfaces should inherit.
- `console/src/app/layout.tsx` and `console/src/app/globals.css`: provide the current metadata, typography, and UI-system baseline for any trust-boundary disclosure work.

### Established Patterns
- Nebula already separates immediate request evidence from persisted ledger evidence; Phase 6 should apply the same clarity to hosted freshness versus local runtime truth.
- Prior phases repeatedly favored explicit operator visibility over hidden automation, which supports making the trust boundary visible in-product rather than only documenting it externally.
- The product is already opinionated about one supported self-hosted deployment path, so hosted positioning should remain additive instead of fragmenting the deployment story.
- Governance hardening established that visible controls should correspond to real authority; Phase 6 should mirror that by making hosted visibility clearly non-authoritative for local runtime behavior.

### Integration Points
- Hosted-boundary language will extend `docs/architecture.md`, `docs/self-hosting.md`, and later pilot/demo docs rather than creating a separate disconnected product story.
- Trust-boundary disclosure UI should align with the current console shell and eventual hosted deployment-detail surfaces, not a marketing-style landing page.
- Status terminology chosen here will constrain the later hosted inventory and deployment-detail contracts in Phases 8 and 10.
- The default metadata contract defined here will constrain later enrollment, heartbeat, and remote-action schemas in Phases 7 through 9.

</code_context>

<deferred>
## Deferred Ideas

- Exact enrollment UX and identity lifecycle details — Phase 7.
- Hosted inventory pages, compatibility badges, and freshness implementation details — Phase 8.
- The first concrete remote-management action and its audit mechanics — Phase 9.
- Broader hosted auth, RBAC, self-serve signup, billing, and enterprise packaging — future phases.

</deferred>

---

*Phase: 06-trust-boundary-and-hosted-contract*
*Context gathered: 2026-03-18*
