---
estimated_steps: 4
estimated_files: 4
skills_used:
  - react-best-practices
---

# T01: Extract shared fleet posture and bounded-action derivation

**Slice:** S02 — Fleet posture UX
**Milestone:** M004

## Description

Create the shared truth seam for S02 by deriving fleet posture and bounded-action availability from existing deployment metadata in one pure module. This task should centralize the rules that classify pending, linked/current, stale, offline, revoked, unlinked, and bounded-action-blocked states so later UI work can render summaries and row cues without reimplementing logic.

## Steps

1. Add `console/src/components/deployments/fleet-posture.ts` with pure helpers that compute fleet-level counts/groups and per-deployment posture details from `DeploymentRecord[]`, using only existing enrollment, freshness, capability, dependency, and remote-action fields.
2. Move the bounded-action disabled-reason logic out of `console/src/components/deployments/remote-action-card.tsx` into the shared helper (or a helper exported from the new module) so the detail card and upcoming summary/table consume the same fail-closed semantics.
3. Write focused Vitest coverage in `console/src/components/deployments/fleet-posture.test.ts` for mixed fleets, pending/null freshness behavior, stale/offline grouping, and bounded-action availability/block reasons.
4. Update `console/src/components/deployments/remote-action-card.test.tsx` as needed so it still proves the card renders the shared blocked reasons and bounded-action wording correctly after the extraction.

## Must-Haves

- [ ] Shared posture helpers derive S02-required states from existing `DeploymentRecord` facts only; no new backend enums, API fields, or hosted-authority language are introduced.
- [ ] `RemoteActionCard` consumes the shared bounded-action reason helper so blocked-state truth is not duplicated across components.
- [ ] Tests cover pending enrollment vs stale/offline visibility and the fail-closed bounded-action cases for stale, offline, revoked, unlinked, and unsupported deployments.

## Verification

- `npm --prefix console run test -- --run src/components/deployments/fleet-posture.test.ts src/components/deployments/remote-action-card.test.tsx`
- `rg -n "Rotation is blocked|Rotation is unavailable|pending enrollment|stale|offline" console/src/components/deployments`

## Observability Impact

- Signals added/changed: one shared derived-state model for fleet counts and bounded-action disabled reasons replaces component-local branching.
- How a future agent inspects this: read `console/src/components/deployments/fleet-posture.ts` and run the focused Vitest files to see whether a failure comes from derivation or rendering.
- Failure state exposed: incorrect blocked reasons or fleet counts become isolated in helper tests before they cascade into page/table regressions.

## Inputs

- `console/src/lib/admin-api.ts` — defines `DeploymentRecord`, enrollment states, freshness states, and remote action fields the helper must consume.
- `console/src/components/deployments/remote-action-card.tsx` — current source of bounded-action disabled-state logic to extract.
- `console/src/components/deployments/remote-action-card.test.tsx` — current proof for fail-closed remote action behavior.
- `console/src/lib/hosted-contract.ts` — wording guardrails the helper-backed UI must preserve.

## Expected Output

- `console/src/components/deployments/fleet-posture.ts` — new shared posture and bounded-action derivation helpers.
- `console/src/components/deployments/fleet-posture.test.ts` — focused tests proving mixed-fleet posture counts and blocked-state semantics.
- `console/src/components/deployments/remote-action-card.tsx` — updated to consume shared bounded-action logic.
- `console/src/components/deployments/remote-action-card.test.tsx` — aligned with the extracted helper-based behavior.
