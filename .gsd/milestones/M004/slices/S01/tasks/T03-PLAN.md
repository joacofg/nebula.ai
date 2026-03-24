---
estimated_steps: 5
estimated_files: 4
skills_used:
  - react-best-practices
  - best-practices
---

# T03: Align deployment-facing hosted action copy and publish the slice boundary artifact

**Slice:** S01 — Hosted reinforcement boundary
**Milestone:** M004

## Description

Close the highest-risk wording seam by aligning deployment-management hosted copy with the shared trust-boundary language, then publish a concise slice artifact that downstream S02 and S03 executors can reuse. This task should keep the hosted action story explicitly bounded to audited credential rotation and document the acceptance rules for future fleet-posture and proof work.

## Steps

1. Update `console/src/components/deployments/remote-action-card.tsx` to use phrasing derived from `console/src/lib/hosted-contract.ts`, keeping the card explicit that hosted can queue one bounded credential-rotation action only and does not gain broader operational authority.
2. If `console/src/app/(console)/deployments/page.tsx` contains deployment-management explainer copy that should reinforce the same boundary, align it to the shared wording without introducing actual fleet-posture synthesis reserved for S02.
3. Extend `console/src/components/deployments/remote-action-card.test.tsx` to lock the refined bounded-action wording and preserve fail-closed semantics for stale, offline, revoked, unlinked, and unsupported deployments.
4. Write `docs/hosted-reinforcement-boundary.md` as the slice artifact documenting allowed hosted reinforcement claims, prohibited authority implications, and the acceptance rules S02/S03 must preserve.
5. Run a targeted wording drift sweep so console and docs surfaces use compatible metadata-only, non-authoritative language.

## Must-Haves

- [ ] Deployment-facing hosted copy stays explicitly bounded to the existing audited credential-rotation action and does not imply broader remote control.
- [ ] The task does not add fleet posture synthesis or new deployment-state logic; it only aligns wording and publishes the slice boundary artifact.
- [ ] `docs/hosted-reinforcement-boundary.md` gives downstream executors a concrete, reusable contract instead of forcing them to reconstruct the guardrails from roadmap prose.

## Verification

- `npm --prefix console run test -- --run src/components/deployments/remote-action-card.test.tsx`
- `pytest tests/test_remote_management_api.py -q`
- `rg -n "metadata-only|request-serving path|local runtime authority|serving traffic|tenant policy|provider credentials|fleet posture|confidence" console/src docs`
- `test -f docs/hosted-reinforcement-boundary.md`

## Observability Impact

- Signals added/changed: clearer bounded-action and non-authority copy on deployment-management surfaces plus a durable slice artifact for future verification
- How a future agent inspects this: run the focused remote-action Vitest and pytest files, then inspect `console/src/components/deployments/remote-action-card.tsx`, `console/src/app/(console)/deployments/page.tsx`, and `docs/hosted-reinforcement-boundary.md`
- Failure state exposed: copy drift or broadened hosted-control implications surface as failing wording assertions, backend fail-closed regressions, or grep-visible conflicts

## Inputs

- `console/src/lib/hosted-contract.ts` — canonical shared hosted reinforcement wording from T01
- `console/src/components/deployments/remote-action-card.tsx` — deployment-facing bounded-action UI
- `console/src/components/deployments/remote-action-card.test.tsx` — current fail-closed and wording assertions
- `console/src/app/(console)/deployments/page.tsx` — deployment-management page copy that may need boundary alignment
- `tests/test_remote_management_api.py` — backend fail-closed proof for bounded hosted actions
- `docs/` — documentation location for the slice boundary artifact

## Expected Output

- `console/src/components/deployments/remote-action-card.tsx` — deployment card copy aligned to the shared hosted boundary
- `console/src/components/deployments/remote-action-card.test.tsx` — focused tests locking the refined bounded-action wording
- `console/src/app/(console)/deployments/page.tsx` — deployment-management explainer copy aligned where needed
- `docs/hosted-reinforcement-boundary.md` — canonical slice artifact for downstream S02/S03 trust-boundary reuse
