# Slice Research — M004 / S02: Fleet posture UX

## Summary
S02 directly owns **R032, R033, R035, and R036**, and it must preserve the S01 guardrails that materially advance **R034**. The slice is mostly a console UX integration slice, not a backend capability slice: the current deployment API already exposes the raw facts needed for a truthful posture layer across multiple deployments (`enrollment_state`, `freshness_status`, `freshness_reason`, `last_seen_at`, `dependency_summary`, `remote_action_summary`, `capability_flags`).

The main gap is not data availability; it is **lack of synthesis at the deployments entrypoint**. `console/src/app/(console)/deployments/page.tsx` currently renders a header, the inventory table, and the detail/create drawer split, but there is no fleet-level summary layer. `console/src/components/deployments/deployment-table.tsx` is still inventory-only: name, environment, freshness, version, last seen. Operators must click into a drawer to understand enrollment state, blocked action states, and dependency posture. That is exactly the ambiguity called out by R032/R033/R036.

The safest implementation path is to keep S02 entirely on the hosted console side and derive posture summaries from existing `DeploymentRecord` facts using shared helper logic/components. Do **not** invent new backend status enums or hosted-authority language. S01 already established the rule: derive wording from `console/src/lib/hosted-contract.ts` and keep posture phrased as metadata-backed, descriptive, and non-authoritative.

## Recommendation
Build S02 around a **new fleet posture summary layer on the deployments page**, backed by small, pure derivation helpers and one or two focused UI components, then lightly upgrade the table to make state legible without losing the current drawer workflow.

Recommended build order:
1. **Create posture derivation helpers first** — one pure module that maps `DeploymentRecord[]` into fleet posture counts/groups and one per-deployment interpretation helper for legible labels/reasons. This is the riskiest seam because it controls truthfulness and wording.
2. **Add a page-level fleet posture summary component** to `console/src/app/(console)/deployments/page.tsx` (or a sibling component under `console/src/components/deployments/`). This should surface at-a-glance counts for linked/active, pending enrollment, stale/offline, and bounded-action blocked states, with copy anchored to the hosted contract.
3. **Upgrade the inventory table** to expose the most important per-row interpretation signals directly at scan time: enrollment state and/or a posture summary column, plus blocked-action cues. Avoid turning it into a dense ops dashboard.
4. **Keep detail drawer and remote action card mostly intact**; only thread in any new shared helpers if needed. The remote-action card already encodes fail-closed behavior and should remain the detailed bounded-action surface.
5. **Lock behavior with focused Vitest** at the derivation-helper, summary-component, and table level.

This matches the `react-best-practices` skill guidance already installed in the project: prefer small pure derivation seams over burying derived UI state inside large page components, and keep component responsibilities narrow so test coverage can validate behavior without full-page integration complexity.

## Implementation Landscape

### Existing files and what they do
- `console/src/app/(console)/deployments/page.tsx`
  - Current hosted deployments entrypoint.
  - Owns TanStack Query fetch/mutation wiring for list/create/token/revoke/unlink.
  - Renders header copy, then `DeploymentTable`, then either `CreateDeploymentSlotDrawer` or `DeploymentDetailDrawer`.
  - Already consumes `getHostedContractContent()` and uses `reinforcement.operatorReadingGuidance[2]` + `allowedDescriptiveClaims[4]` in header copy.
  - Natural seam for adding a new top-of-page fleet posture summary above the table.

- `console/src/components/deployments/deployment-table.tsx`
  - Current scan surface for inventory only.
  - Columns: Name, Environment, Freshness, Version, Last Seen.
  - Handles empty state and selected-row styling.
  - Already visually dims stale/offline rows, but does not show enrollment state or blocked bounded-action state.
  - Natural seam for adding one or two additional columns or a compact posture cell if summary logic stays out of the component.

- `console/src/components/deployments/deployment-detail-drawer.tsx`
  - Rich per-deployment detail view.
  - Shows freshness badge/reason/date, identity fields, capability flags, enrollment state, dependencies, trust-boundary card, remote action card, lifecycle actions.
  - Important constraint: the drawer already contains a lot of interpretive detail. S02 should not depend on the drawer for primary fleet reading; instead it should let operators decide which drawer to open after scanning the new posture layer.

- `console/src/components/deployments/remote-action-card.tsx`
  - Current detailed bounded hosted action UI.
  - Encodes fail-closed rules for pending/revoked/unlinked/stale/offline/unsupported deployments through `getDisabledReason()`.
  - Pulls shared phrasing from `getHostedContractContent().reinforcement.boundedActionPhrasing.description`.
  - Strong existing seam for bounded-action availability truth. S02 should reuse this logic or extract it, not reimplement subtly different blocked-state rules in a second place.

- `console/src/lib/hosted-contract.ts`
  - Canonical trust-boundary and reinforcement vocabulary seam from S01.
  - Key strings to reuse:
    - `reinforcement.allowedDescriptiveClaims`
    - `reinforcement.operatorReadingGuidance`
    - `reinforcement.boundedActionPhrasing`
  - Important rule from S01: do not create a deployments-only wording island for posture semantics.

- `console/src/lib/admin-api.ts`
  - Frontend contract for `DeploymentRecord`, including all status facts S02 needs.
  - `DeploymentRecord` fields already present for posture UX:
    - `enrollment_state`
    - `freshness_status`
    - `freshness_reason`
    - `last_seen_at`
    - `dependency_summary`
    - `remote_action_summary`
    - `capability_flags`
  - No obvious missing frontend contract field blocks S02.

- `console/src/lib/freshness.ts`
  - Maps freshness status to labels/styles and formats `last_seen_at`.
  - Important behavior: `null` freshness maps to `Awaiting enrollment`; `last_seen_at === null` maps to `Never`.
  - Useful for posture derivation because pending/never-enrolled deployments already have a consistent UI interpretation.

- `console/src/components/deployments/deployment-status-badge.tsx`
  - Canonical UI labels for enrollment state: Pending enrollment, Active, Revoked, Unlinked.
  - Reuse this badge rather than hand-rolling enrollment-state text in posture cards/table rows.

- `console/src/components/deployments/dependency-health-pills.tsx`
  - Renders coarse dependency summaries from backend metadata.
  - Useful if S02 wants a compact “degraded dependencies present” cue, but avoid dumping pill sets into the top summary unless needed.

### Backend/data model facts that constrain the UI
- `src/nebula/models/deployment.py`
  - Confirms the backend contract already supports all required deployment states for S02.
  - `EnrollmentState = "pending" | "active" | "revoked" | "unlinked"`
  - `freshness_status` is nullable specifically for pending/never-seen deployments.
  - `remote_action_summary` is already available if the UI wants to show recent queued/applied/failed context.

- `tests/test_freshness.py`
  - Confirms freshness semantics are time-based only:
    - connected: within 10m
    - degraded: 10–30m
    - stale: 30–60m
    - offline: >60m
    - pending/never-enrolled: `(None, None)`
  - Important wording guardrail: reasons should be time-based only and avoid inferred causal/authority words like healthy/running/stable.
  - S02 posture labels should follow the same discipline.

- `tests/test_remote_management_api.py`
  - Confirms the backend fail-closes remote actions for non-active deployments and supports history listing.
  - UI should treat remote-action blocking as descriptive evidence, not local policy authority.

### What is already tested
- `console/src/components/deployments/deployment-table.test.tsx`
  - Currently locks the inventory-only table columns and empty state.
  - This file will need meaningful updates if the table gains posture/state columns.

- `console/src/components/deployments/remote-action-card.test.tsx`
  - Already locks the detailed bounded-action wording and blocked reasons for stale/offline/revoked/unlinked/unsupported deployments.
  - Best source of truth for blocked-state semantics when designing posture summaries.

- `console/src/lib/hosted-contract.test.ts`
  - Already verifies required S01 phrasing, including:
    - “Hosted fleet posture describes what deployments most recently reported...”
  - S02 should not bypass this seam.

## Natural seams for task decomposition
1. **Pure derivation seam**
   - Likely new file, e.g. `console/src/components/deployments/fleet-posture.ts` or `console/src/lib/deployment-posture.ts`.
   - Responsibilities:
     - compute fleet-level counts/groups from `DeploymentRecord[]`
     - compute per-deployment interpreted posture labels/reasons from existing facts
     - possibly centralize bounded-action block derivation so summary/table and remote-action card share truth
   - Best first task because it de-risks wording and truthfulness before UI composition.

2. **Fleet summary UI seam**
   - Likely new component under `console/src/components/deployments/`.
   - Renders summary cards/banners for:
     - linked/active
     - pending enrollment
     - stale or offline visibility
     - bounded-action blocked deployments
   - Should consume the pure derivation output + hosted contract wording.

3. **Table legibility seam**
   - Update `deployment-table.tsx` and its test.
   - Add enrollment-state legibility and/or a compact posture/action-status column.
   - Keep row click/select behavior unchanged.

4. **Page wiring seam**
   - Update `page.tsx` to compute derived posture from `deploymentsQuery.data ?? []` and pass data into the new summary component.
   - Keep existing mutation/query wiring stable.

5. **Optional detail/drawer follow-through seam**
   - Only if needed to reuse extracted helpers or align labels. Avoid broad rework here.

## Truthfulness and wording constraints
- Reuse `getHostedContractContent()` for user-visible explanatory copy. S01 explicitly established this as the canonical seam.
- Do not describe hosted posture as health certification. The allowed claim is: hosted posture describes what deployments most recently reported.
- Prefer labels like **pending enrollment**, **linked**, **stale visibility**, **offline visibility**, **bounded action blocked**, **action unavailable**, **action eligible** over adjectives like healthy, verified, safe, or ready.
- Keep local-runtime caveats near any high-level summary, especially if the summary compresses “current enough to trust as current” into a friendly label.
- Freshness null means “awaiting enrollment” / “never reported”, not “offline”. The code and tests already encode this distinction.
- If blocked-action counts are summarized, they should describe hosted bounded-action availability only; do not imply broader remote control.

## Likely implementation approach
A low-risk posture model from existing facts would be:
- **Pending enrollment**: `enrollment_state === "pending"`
- **Linked**: `enrollment_state === "active"`
- **Revoked / unlinked**: explicit non-linked terminal states
- **Current enough to trust as current**: active + freshness in `connected | degraded`
  - But copy should still say “reported recently” or similar, not “healthy” or “serving normally”.
- **Stale visibility**: active + freshness `stale`
- **Offline visibility**: active + freshness `offline`
- **Bounded action blocked**:
  - non-active deployments
  - stale/offline deployments
  - active deployments without `remote_credential_rotation`
- **Bounded action available**:
  - active + freshness not stale/offline + capability present

This can all be derived client-side with no API change.

## Risks / gotchas for the planner
- **Do not fork blocked-action logic** in multiple components. Right now `remote-action-card.tsx` owns `getDisabledReason()`. If S02 needs the same semantics in summary/table, extract that into a shared helper rather than duplicating conditions.
- **Do not overfit the top summary to dependency pills.** `dependency_summary` exists, but turning the summary strip into a mini NOC dashboard would violate milestone framing. A small “degraded dependencies present” cue may be enough if needed.
- **Table width pressure is real.** The current table already has five columns. Adding too many columns will make the scan surface worse. A single compact “Posture” or “Link state” column is likely safer than multiple new columns.
- **Keep the empty state simple.** No deployments linked is still a valid empty fleet posture. Do not add posture cards that look broken for the empty case.
- **Do not reintroduce S01 wording drift.** Any new explanatory copy on the deployments page or summary cards should cite/reuse the hosted-contract seam.

## Verification
Frontend-focused verification should be sufficient for S02 unless implementation changes the API contract.

Recommended checks:
- `npm --prefix console run test -- --run src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx src/lib/hosted-contract.test.ts`
- Add and run focused tests for any new helper/component, e.g.:
  - `src/components/deployments/fleet-posture.test.ts`
  - `src/components/deployments/fleet-posture-summary.test.tsx`
  - or equivalent final file names
- Grep wording drift / posture terms:
  - `rg -n "fleet posture|metadata-backed|descriptive only|local runtime|bounded|pending enrollment|stale|offline|unlinked|revoked" console/src docs`

If a page-level test is added, also run it explicitly. Existing patterns suggest focused Vitest is the right granularity.

## Skill discovery
Installed skills already directly relevant:
- `react-best-practices` — use for component factoring, avoiding unnecessary client complexity, and keeping derived UI state in pure helpers.
- `frontend-design` and `make-interfaces-feel-better` — potentially useful if the summary layer needs visual hierarchy/polish, but not essential for slice truthfulness.

Promising external skills discovered but **not installed**:
- Next.js: `wshobson/agents@nextjs-app-router-patterns` — install with `npx skills add wshobson/agents@nextjs-app-router-patterns`
- React: `vercel-labs/agent-skills@vercel-react-best-practices` — install with `npx skills add vercel-labs/agent-skills@vercel-react-best-practices`
- TanStack Query: `jezweb/claude-skills@tanstack-query` — install with `npx skills add jezweb/claude-skills@tanstack-query`

These are optional; S02 does not appear blocked on missing skill coverage.

## Recommendation to planner
Plan S02 as a **light-to-targeted console slice**:
- no backend contract expansion unless implementation proves an actual gap,
- first extract/posture-derive shared truth from `DeploymentRecord`,
- then add a fleet posture summary component,
- then update the table for at-a-glance legibility,
- then lock behavior with focused Vitest.

The slice should prove that hosted can truthfully summarize fleet posture from existing metadata, not that hosted gained new authority or richer ops telemetry.
