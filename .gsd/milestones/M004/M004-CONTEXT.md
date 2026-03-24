# M004: Hosted Adoption Reinforcement

**Gathered:** 2026-03-24
**Status:** Ready for planning

## Project Description

Create M004: Hosted Adoption Reinforcement. Improve Nebula’s hosted and control-plane adoption touches only where they make onboarding, fleet understanding, and operator confidence materially better, while preserving the metadata-only trust boundary and keeping local runtime enforcement authoritative. The milestone is about reinforcement, not authority. Hosted improvements should help teams understand deployment state, onboarding readiness, rollout posture, or operator trust without introducing hosted-plane dependency for serving-time behavior.

## Why This Milestone

Nebula already has meaningful hosted/control-plane prior art: deployment slot creation, enrollment-token flow, linked deployment inventory, freshness states, dependency summaries, bounded remote action history, and a public trust-boundary explanation. What is still weak is the fleet-reading experience. The current hosted side reads more like inventory plus per-deployment detail than a clear, non-authoritative fleet posture surface for evaluators and operators working across multiple deployments.

This milestone exists to make hosted adoption reinforcement materially better without violating the hosted/local trust model. The hosted console should become easier to read, easier to compare across deployments, and more confidence-building, but it must never feel like the source of truth for serving-time health, routing, fallback, or policy authority. Adoption clarity still matters more than feature count.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Open the hosted console and quickly understand fleet posture across multiple deployments: what is linked, what is pending, what is current enough to trust as current, what is stale or offline, and what bounded hosted actions are blocked.
- Follow one integrated proof showing that hosted surfaces reinforce onboarding clarity and operator confidence while local runtime enforcement remains authoritative and hosted remains metadata-only by default.

### Entry point / environment

- Entry point: hosted deployment management surfaces in the Next.js console plus supporting trust-boundary and proof docs under `docs/`
- Environment: browser-based console and documentation, grounded in the existing self-hosted runtime plus optional hosted control-plane model
- Live dependencies involved: console deployment inventory and detail views, hosted contract module and schema, backend deployment/hosted metadata models, and existing bounded remote-action/admin API flows

## Completion Class

- Contract complete means: the hosted reinforcement semantics are explicit in UI copy, docs, tests, and planning guardrails, and they stay aligned to the metadata-only hosted contract.
- Integration complete means: the hosted console, trust-boundary wording, deployment status interpretation, and integrated proof all agree on what the hosted plane knows, what it does not control, and how a multi-deployment operator should read fleet posture.
- Operational complete means: hosted visibility can age, degrade, or go offline without breaking the self-hosted serving path, and the milestone proves that the UX still explains that truth clearly.

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- A multi-deployment evaluator can use the hosted console to understand fleet posture quickly without mistaking hosted status for local runtime authority.
- A bounded hosted remote action remains visibly narrow, fail-closed, and easier to interpret in context.
- The final integrated walkthrough shows hosted reinforcement improving adoption and confidence without moving serving-time behavior, runtime policy, prompts, responses, or provider credentials into hosted authority.

## Risks and Unknowns

- Better summaries can accidentally imply authority — if fleet posture or confidence language reads like hosted certification of runtime truth, the milestone regresses the trust boundary instead of improving it.
- Existing metadata may not be enough for a truthful fleet posture summary — if the current data model cannot support the intended summary layer, there is a risk of pressure to add interpretive or authority-adjacent state.
- The hosted console could become noisier instead of clearer — status and confidence cues need to compress meaning, not create another dashboard that operators have to decode.

## Existing Codebase / Prior Art

- `console/src/app/(console)/deployments/page.tsx` — current hosted deployment inventory page; today it manages a table plus detail/create drawer split, but it lacks a true fleet posture summary layer.
- `console/src/components/deployments/deployment-table.tsx` — current table surface for name, environment, freshness, version, and last seen; useful inventory, limited synthesis.
- `console/src/components/deployments/deployment-detail-drawer.tsx` — per-deployment detail view with freshness, dependency summary, trust-boundary card, and lifecycle actions.
- `console/src/components/deployments/remote-action-card.tsx` — bounded hosted remote-action UI with fail-closed rules already encoded for stale, offline, revoked, unlinked, and unsupported cases.
- `console/src/lib/hosted-contract.ts` — shared hosted trust-boundary vocabulary and schema-backed exported-field list; already states metadata-only by default, outage behavior, freshness meaning, and remote-management safety limits.
- `console/src/app/trust-boundary/page.tsx` — public trust-boundary page explaining hosted optionality, visibility-only outages, and the default hosted contract.
- `src/nebula/models/hosted_contract.py` — backend source of truth for the metadata-only default export contract.
- `src/nebula/models/deployment.py` — deployment record and remote-action shapes used by the hosted surfaces.

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R014 — Hosted/control-plane surfaces grow only where they materially improve adoption and operator confidence beyond the current metadata-only support model.
- R032 — Hosted console gives a clear fleet posture view across linked deployments without implying hosted authority.
- R033 — Operators can quickly distinguish linked, pending, stale, offline, and blocked deployment states from the hosted console.
- R034 — Hosted fleet summaries stay grounded in metadata-only facts and explicitly avoid serving-time or policy authority claims.
- R035 — The hosted console makes bounded hosted action availability and blocking reasons legible without implying broader remote control.
- R036 — Hosted onboarding and linkage state become easier to interpret for multi-deployment evaluators adopting Nebula across more than one deployment.
- R037 — Nebula provides an integrated proof showing hosted surfaces reinforce adoption and operator confidence while local runtime enforcement remains authoritative.
- R038 — Hosted adoption reinforcement improves operator confidence through clearer status interpretation, freshness meaning, and evidence framing.

## Scope

### In Scope

- Hosted console UX improvements that make fleet posture easier to read across multiple deployments.
- Clearer interpretation of linkage, enrollment, freshness, dependency summary, and bounded remote-action availability.
- Trust-boundary wording and proof updates needed to keep the new UX clearly descriptive and non-authoritative.
- A canonical integrated proof for hosted adoption reinforcement.
- Small metadata-shape adjustments only if needed to support truthful posture summaries from already legitimate hosted facts.

### Out of Scope / Non-Goals

- Hosted-plane runtime enforcement.
- Remote serving control beyond the already approved bounded action.
- Broad hosted product expansion unrelated to adoption reinforcement.
- New dependency on hosted services for local gateway correctness.
- Commercial packaging, billing, or enterprise-access redesign.
- Hosted features that weaken the local-authority trust model.
- A generic operations dashboard that tries to replace local runtime truth.

## Technical Constraints

- Preserve the metadata-only trust boundary by default. Raw prompts, raw responses, provider credentials, raw usage-ledger rows, tenant secrets, and authoritative runtime policy state remain excluded from the hosted default contract.
- Keep local runtime enforcement authoritative. Hosted visibility may be stale or offline without changing local serving correctness.
- Prefer fleet posture and confidence language over headline readiness language so the hosted console stays descriptive rather than authoritative.
- Prefer composition over expansion: use existing deployment, freshness, dependency, and remote-action facts first; any added metadata must clarify the same bounded reality rather than create new control semantics.
- Optimize for the multi-deployment evaluator/operator case first. Single-deployment pilots should benefit as a simpler subset.

## Integration Points

- Hosted deployment console surfaces — where the fleet posture UX will live.
- Hosted trust-boundary module and public trust-boundary page — where language and contract clarity must stay aligned.
- Backend deployment record and hosted contract models — the factual source of what the hosted plane can show.
- Existing admin/deployment APIs and remote-action flows — bounded behavior that must remain clearly narrow and fail-closed.
- Documentation and proof artifacts under `docs/` — where the integrated hosted/local trust story must be assembled.

## Open Questions

- Is the current deployment metadata enough for a truthful fleet posture summary, or does the UI need one or two additional descriptive fields? — Current thinking: stay with existing facts first; only add narrowly descriptive metadata if the summary would otherwise be misleading or too implicit.
- How much “confidence” language is safe before it starts to sound like hosted certification? — Current thinking: use confidence as an operator-feeling outcome, but keep the UI anchored to concrete descriptive facts such as linkage, freshness age, and bounded-action eligibility.
