# S01 Research — Hosted reinforcement boundary

## Summary

S01 directly targets **R034** and partially retires **R014** by locking the allowed hosted reinforcement vocabulary before any fleet-posture UI work lands. It also supports downstream work on **R032/R033/R035/R036/R037/R038** because the same trust-boundary language is already shared across the deployments page, deployment detail drawer, remote-action copy, and public trust-boundary page.

This slice is **targeted research**, not deep architecture work. The codebase already has the core seams: a schema-backed hosted contract module (`console/src/lib/hosted-contract.ts`), a public trust-boundary page (`console/src/app/trust-boundary/page.tsx`), a reusable trust-boundary card (`console/src/components/hosted/trust-boundary-card.tsx`), deployment inventory/detail surfaces, and fail-closed remote-action behavior. What is missing is an explicit milestone-level reinforcement vocabulary and guardrails that downstream S02/S03 work can reuse without drifting into hosted authority language.

The riskiest issue is **semantic drift, not missing plumbing**: current copy is accurate but fragmented. The trust-boundary module says “metadata-only by default” and “not in the request-serving path,” while the deployments page and remote-action card use narrower local copy. S01 should centralize/lock the phrases that future fleet-posture summaries are allowed to imply and the claims they must avoid.

## Recommendation

Build S01 around the **existing hosted-contract content module as the canonical wording seam**. Do not invent a parallel constants file in the deployments feature. Extend the hosted-contract module to expose milestone-specific reinforcement guardrails and vocabulary that can be consumed by:

- `console/src/app/trust-boundary/page.tsx`
- `console/src/components/hosted/trust-boundary-card.tsx`
- deployment-facing explanatory UI in `console/src/app/(console)/deployments/page.tsx`
- bounded-action framing in `console/src/components/deployments/remote-action-card.tsx`
- any slice-proof docs under `docs/`

Treat S01 output as a **descriptive language contract**, not a UI redesign. The planner should sequence work as:
1. lock vocabulary/guardrails in the shared module and docs/tests first,
2. then wire those phrases into existing console surfaces,
3. then record the proof artifact for planners/executors downstream.

This follows the repo’s existing pattern of **schema-backed contract + focused tests**, and aligns with the loaded `react-best-practices` / `best-practices` skills: prefer composition over duplicate state, and constrain language through reusable modules instead of copy-paste strings.

## Implementation Landscape

### Existing files and what they do

- `console/src/lib/hosted-contract.ts`
  - Current canonical frontend trust-boundary module.
  - Imports `docs/hosted-default-export.schema.json` and derives exported-field labels from schema order.
  - Already exposes:
    - excluded-by-default data classes,
    - freshness vocabulary,
    - shared copy for onboarding, outage behavior, remote-management limits,
    - parity checks that fail fast on schema drift.
  - Best existing seam for S01.

- `console/src/lib/hosted-contract.test.ts`
  - Locks schema parity, excluded field list, freshness enum, and all copy strings.
  - This is the natural place to add tests for any new reinforcement/guardrail copy.

- `console/src/components/hosted/trust-boundary-card.tsx`
  - Reusable UI card rendering the hosted contract summary.
  - Already communicates:
    - metadata-only by default,
    - not in request path,
    - freshness states,
    - excluded data,
    - warning that hosted freshness is not runtime authority.
  - Likely should render any new “allowed hosted posture claims” or “what hosted does not certify” content if S01 needs visible guardrails.

- `console/src/components/hosted/trust-boundary-card.test.tsx`
  - Focused assertions for trust-boundary card wording.
  - Useful for regression-locking any visible new guardrail bullets.

- `console/src/app/trust-boundary/page.tsx`
  - Public page that explains hosted optionality, outages-as-visibility-only, onboarding flow, and bounded remote-management safety limits.
  - This is where milestone-level trust narrative can be made explicit for S03 proof reuse.

- `console/src/app/trust-boundary/page.test.tsx`
  - Locks the public trust-boundary page copy and section presence.

- `console/src/app/(console)/deployments/page.tsx`
  - Current console entry point for deployment inventory plus detail/create drawer split.
  - No fleet posture summary layer yet; header copy is operational but generic.
  - Good integration point for a compact non-authoritative posture explainer or vocabulary callout once S02 starts.

- `console/src/components/deployments/deployment-table.tsx`
  - Current inventory table only: name, environment, freshness, version, last seen.
  - No synthesized posture interpretation.
  - Important constraint for S01: avoid adding authority semantics here yet; save actual posture synthesis for S02.

- `console/src/components/deployments/deployment-detail-drawer.tsx`
  - Per-deployment detail surface.
  - Shows freshness, enrollment state, dependencies, trust-boundary card, and remote-action card.
  - Already wires trust boundary adjacent to operational details, which is the correct seam for downstream posture interpretation.

- `console/src/components/deployments/remote-action-card.tsx`
  - Bounded hosted action UI for `rotate_deployment_credential` only.
  - Encodes fail-closed rules for pending/revoked/unlinked/stale/offline/unsupported deployments.
  - Current explanatory copy is strong but local: “does not change serving traffic, tenant policy, or provider credentials.”
  - S01 should align this wording with the shared hosted-contract vocabulary, not let it drift independently.

- `console/src/components/deployments/remote-action-card.test.tsx`
  - Already locks fail-closed behavior and blocking reasons.
  - Natural place to assert any refined “bounded action only” wording if changed.

- `src/nebula/models/hosted_contract.py`
  - Backend source of truth for the default hosted metadata contract.
  - Exposes the exact allowed exported fields and excluded data classes.
  - S01 should not widen this unless a wording/proof need reveals a real contract mismatch.

- `tests/test_hosted_contract.py`
  - Backend guard for exact allowed fields, exact freshness enum, exact excluded classes, and schema artifact parity.
  - Critical verification seam if any contract wording or schema artifact references change.

- `src/nebula/models/deployment.py`
  - Defines deployment/enrollment/remote-action response shapes for hosted surfaces.
  - Relevant because downstream S02 posture work must stay grounded in these existing facts: `enrollment_state`, `freshness_status`, `freshness_reason`, `dependency_summary`, `remote_action_summary`.

- `src/nebula/services/heartbeat_ingest_service.py`
  - Defines freshness computation semantics.
  - Important boundary fact: freshness is derived from heartbeat recency only and explicitly returns `(None, None)` for never-enrolled deployments.
  - This means hosted UI can talk about freshness of reported metadata, but not certify runtime health.

- `src/nebula/services/enrollment_service.py`
  - Deployment listing and remote-action queueing behavior.
  - Important boundary fact: remote actions are only allowed for `enrollment_state == "active"`; they are not a general remote control channel.

- `tests/test_remote_management_api.py`
  - Locks backend fail-closed behavior for remote actions on pending/revoked/unlinked deployments.
  - Useful evidence that hosted action semantics are already narrow and enforcement-backed.

### Natural seams for planner decomposition

1. **Shared vocabulary seam**
   - Main file: `console/src/lib/hosted-contract.ts`
   - Work: add explicit reinforcement vocabulary + “may imply / must not imply” guardrails.
   - Independent verification: `console/src/lib/hosted-contract.test.ts`

2. **Public trust-boundary seam**
   - Main files:
     - `console/src/app/trust-boundary/page.tsx`
     - `console/src/components/hosted/trust-boundary-card.tsx`
   - Work: render the new shared guardrails in public-facing explanatory surfaces.
   - Independent verification:
     - `console/src/app/trust-boundary/page.test.tsx`
     - `console/src/components/hosted/trust-boundary-card.test.tsx`

3. **Deployments-surface alignment seam**
   - Main files:
     - `console/src/app/(console)/deployments/page.tsx`
     - `console/src/components/deployments/deployment-detail-drawer.tsx`
     - `console/src/components/deployments/remote-action-card.tsx`
   - Work: align local explanatory copy with the shared hosted vocabulary without yet building S02 posture UI.
   - Independent verification:
     - `console/src/components/deployments/remote-action-card.test.tsx`
     - possible new component/page tests if header/help text is added.

4. **Proof/documentation seam**
   - Likely under `docs/` plus this slice artifact.
   - Work: capture explicit milestone-level guardrails for downstream S03 integrated proof.
   - Verification: file existence/content checks and link consistency.

## Key findings and constraints

### 1. The factual contract is already narrow and well-defended

The backend/frontend contract is already strongly protected:
- backend `HostedDeploymentMetadata` defines exactly 12 exported fields,
- frontend `hosted-contract.ts` imports the generated JSON schema and fails fast on drift,
- backend and frontend tests both assert exact excluded data classes and freshness values.

This means S01 should **not** create a new trust-boundary mechanism. It should build on the existing contract layer.

### 2. Freshness is the core authority-risk area

`src/nebula/services/heartbeat_ingest_service.py` makes freshness purely about the recency of deployment reports. It does **not** mean current serving truth. The shared copy already says “Hosted freshness is not local runtime authority.”

Planner implication: any new vocabulary must keep “current enough to trust as current” scoped to **hosted metadata recency**, not runtime health, routing correctness, fallback correctness, or policy enforcement.

### 3. Remote action semantics are already safely bounded

`remote-action-card.tsx` plus `tests/test_remote_management_api.py` show the only hosted remote action is credential rotation, gated to active linked deployments and blocked for stale/offline/revoked/unlinked/unsupported cases. This already satisfies much of the “bounded action” part of R035.

Planner implication: S01 likely only needs wording alignment here, not backend behavior changes.

### 4. Current risk is wording drift across surfaces

Examples:
- `hosted-contract.ts` says “not in the request-serving path” and “metadata-only by default.”
- deployments page header just says “Manage linked self-hosted Nebula deployments…”
- remote action card says “does not change serving traffic, tenant policy, or provider credentials.”
- trust-boundary page says hosted is “recommended for pilots” and improves “fleet visibility.”

These are directionally aligned but not yet a locked milestone vocabulary. Downstream S02 could easily introduce posture words like “ready,” “healthy,” or “protected” unless S01 constrains the allowed phrases now.

### 5. S01 should avoid prematurely building posture UI

The deployments table is still plain inventory. That is correct for S01. The roadmap says S02 should create the actual fleet posture layer. If S01 starts synthesizing fleet states in `deployment-table.tsx`, it will blur the slice boundary and make it harder to evaluate whether the semantics or the UI caused drift.

### 6. Existing test strategy strongly favors focused copy/component locks

The roadmap explicitly calls for focused Vitest coverage for hosted posture summaries, deployment interpretation components, and trust-boundary wording. This matches existing repo practice: trust-boundary and deployment components already have narrow tests. S01 should continue that style instead of trying to prove wording with broad E2E.

### 7. Local verification is currently environment-blocked in this worktree

Observed during research:
- `npm --prefix console run test -- --run ...` failed because `vitest` is not installed in this worktree environment (`sh: vitest: command not found`).
- `python -m pytest ...` failed because `python` is not available on PATH in this worktree environment.

Planner implication: verification commands are known, but execution may require the repo bootstrap step (`make setup` / npm install) in executor contexts. Research should still specify the intended commands.

## What to build or prove first

1. **First: define explicit guardrail vocabulary in the shared hosted contract module**
   - This is the highest-risk ambiguity and unblocks every later UI/proof task.
   - Good output shape: a structured export such as allowed posture terms, prohibited implication classes, and operator-reading guidance.

2. **Second: render those guardrails on the public trust-boundary surface**
   - This creates the canonical narrative downstream slices can cite.
   - Also gives S03 a stable walkthrough anchor.

3. **Third: align deployments/remote-action local copy to the shared phrasing**
   - Keep changes narrow and descriptive.
   - Do not add posture summaries yet.

4. **Fourth: write the slice doc/proof artifact**
   - Capture explicit acceptance rules for S02/S03 to consume.

## Verification plan

### Primary checks

Frontend focused tests:
- `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts`
- `npm --prefix console run test -- --run src/components/hosted/trust-boundary-card.test.tsx`
- `npm --prefix console run test -- --run src/app/trust-boundary/page.test.tsx`
- `npm --prefix console run test -- --run src/components/deployments/remote-action-card.test.tsx`
- If deployments-page explanatory copy changes, add a page/component test and run it explicitly.

Backend contract checks:
- `pytest tests/test_hosted_contract.py -q`
- `pytest tests/test_remote_management_api.py -q`

Source-level drift checks:
- `rg -n "metadata-only|request-serving path|freshness is not|remote-management safety limits|serving traffic|tenant policy|provider credentials" console/src docs`
- Use this as a review pass to ensure old and new phrases do not conflict.

### What passing should mean

- Shared trust-boundary module exposes the reinforcement vocabulary/guardrails in one place.
- Public trust-boundary page and trust card render the same non-authoritative semantics.
- Remote-action and deployment surfaces do not imply broader hosted control.
- No backend/schema changes widen the hosted export contract.

## Skill discovery

Installed skills already directly relevant:
- `react-best-practices` — relevant for Next.js/React composition and avoiding duplicated copy/state seams.
- `best-practices` — relevant for keeping security/trust-boundary wording precise.

Promising external skills not installed:
- Next.js: `npx skills add wshobson/agents@nextjs-app-router-patterns`
  - Found via `npx skills find "Next.js"`
  - Highest install count among directly relevant Next.js App Router skills.
- TanStack Query: `npx skills add jezweb/claude-skills@tanstack-query`
  - Found via `npx skills find "TanStack Query"`
  - Relevant if S02 later changes deployment data loading patterns.
- Pydantic: `npx skills add bobmatnyc/claude-mpm-skills@pydantic`
  - Found via `npx skills find "Pydantic"`
  - Only marginally relevant for S01 because the backend contract already exists.

## Risks to call out for the planner

- **Authority drift via adjectives**: words like “healthy,” “ready,” “safe,” “verified,” or “protected” would overstate what hosted metadata can prove.
- **Dual-source copy drift**: if S01 adds prose directly in deployments components without routing through `hosted-contract.ts`, S02/S03 will drift fast.
- **Premature S02 work**: adding synthesized fleet summaries in S01 would blur the slice boundary and make it harder to verify semantics first.
- **Verification environment drift**: local tooling was unavailable during research, so executor tasks should budget for environment bootstrap before test execution.

## Concrete planner handoff

If decomposing into execution tasks, the cleanest split is:
1. extend `console/src/lib/hosted-contract.ts` + tests with reinforcement guardrails/vocabulary,
2. wire the new shared content into `console/src/components/hosted/trust-boundary-card.tsx` and `console/src/app/trust-boundary/page.tsx` + tests,
3. align `console/src/components/deployments/remote-action-card.tsx` and optionally `console/src/app/(console)/deployments/page.tsx` / `deployment-detail-drawer.tsx` to the shared wording,
4. add/update doc artifact(s) under `docs/` if the slice implementation chooses a canonical prose file for S03 reuse.
