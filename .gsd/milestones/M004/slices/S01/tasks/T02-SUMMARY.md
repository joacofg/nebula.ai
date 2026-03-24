---
id: T02
parent: S01
milestone: M004
provides:
  - Canonical hosted trust-boundary guardrails rendered on the public card and trust-boundary page from the shared hosted contract seam
key_files:
  - console/src/components/hosted/trust-boundary-card.tsx
  - console/src/components/hosted/trust-boundary-card.test.tsx
  - console/src/app/trust-boundary/page.tsx
  - console/src/app/trust-boundary/page.test.tsx
  - .gsd/milestones/M004/slices/S01/S01-PLAN.md
key_decisions:
  - Reused the shared hosted-contract reinforcement exports directly on both public surfaces, even when that meant repeated phrases, and made the tests assert presence rather than unique rendering
patterns_established:
  - When a page intentionally composes a shared contract card plus page-level narrative from the same wording seam, render tests should tolerate duplicate canonical phrases and verify reuse instead of uniqueness
observability_surfaces:
  - console/src/components/hosted/trust-boundary-card.tsx
  - console/src/app/trust-boundary/page.tsx
  - npm --prefix console run test -- --run src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx
  - npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx src/components/deployments/remote-action-card.test.tsx
  - /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q
duration: 31m
verification_result: passed
completed_at: 2026-03-24T11:26:00-03:00
blocker_discovered: false
---

# T02: Render the canonical trust-boundary guardrails on hosted public surfaces

**Rendered the shared hosted reinforcement guardrails on the trust-boundary card and public page, with focused tests that lock the metadata-only, non-authoritative narrative.**

## What Happened

I updated `console/src/components/hosted/trust-boundary-card.tsx` to consume `reinforcement` from `getHostedContractContent()` and render three shared-content sections beyond the existing export contract details: operator reading guidance, reinforcement guardrails, and bounded-action phrasing. That keeps the card concise while making the canonical hosted fleet-posture and non-authority framing visible in the reusable public surface.

I then updated `console/src/app/trust-boundary/page.tsx` to stop restating custom trust-boundary prose and instead compose its intro and explanatory sections from the same shared hosted-contract exports. The page now reuses canonical allowed descriptive claims, operator guidance, prohibited authority claims, and bounded-action phrasing so the hosted story stays metadata-backed and descriptive only even when hosted data is stale or offline.

I extended the focused tests in `console/src/components/hosted/trust-boundary-card.test.tsx` and `console/src/app/trust-boundary/page.test.tsx` to assert the new rendered sections and shared phrasing. During verification I found the page intentionally renders some of the same shared contract phrases in both the top-level narrative and the embedded card, so I adjusted the page tests to assert presence with `getAllBy*` where reuse is expected instead of incorrectly requiring uniqueness.

## Verification

I ran the task-level frontend verification command, the broader slice frontend verification command, and the backend slice contract tests. I also kept the earlier grep-based wording inspection result in mind from this task run: the request-serving-path, local-runtime-authority, and fleet-posture wording is present in the intended trust-boundary surfaces.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx` | 1 | ❌ fail | ~1s |
| 2 | `rg -n "fleet posture|confidence|local runtime authority|request-serving path" console/src/app/trust-boundary console/src/components/hosted` | 0 | ✅ pass | <1s |
| 3 | `npm --prefix console run test -- --run src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx` | 1 | ❌ fail | ~1s |
| 4 | `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx src/components/deployments/remote-action-card.test.tsx` | 1 | ❌ fail | ~1s |
| 5 | `pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q` | 127 | ❌ fail | <1s |
| 6 | `rg -n "metadata-only|request-serving path|local runtime authority|serving traffic|tenant policy|provider credentials|fleet posture|confidence" console/src docs` | 0 | ✅ pass | <1s |
| 7 | `test -f docs/hosted-reinforcement-boundary.md` | 1 | ❌ fail | <1s |
| 8 | `npm --prefix console run test -- --run src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx` | 1 | ❌ fail | ~1s |
| 9 | `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx src/components/deployments/remote-action-card.test.tsx` | 1 | ❌ fail | ~1s |
| 10 | `python -m pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q` | 127 | ❌ fail | <1s |
| 11 | `npm --prefix console run test -- --run src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx` | 0 | ✅ pass | ~1s |
| 12 | `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx src/components/deployments/remote-action-card.test.tsx` | 0 | ✅ pass | ~1s |
| 13 | `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q` | 0 | ✅ pass | ~2s |

## Diagnostics

Inspect `console/src/components/hosted/trust-boundary-card.tsx` for the card-level rendering of shared reading guidance, reinforcement guardrails, and bounded-action phrasing from `getHostedContractContent()`. Inspect `console/src/app/trust-boundary/page.tsx` for the page-level composition of shared allowed claims, operator guidance, prohibited claims, and outage copy. The focused Vitest files surface copy drift as exact failing render assertions, while backend alignment remains visible through `tests/test_hosted_contract.py` and `tests/test_remote_management_api.py`.

## Deviations

Used the repo venv pytest binary (`/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/pytest`) instead of bare `pytest` because the worktree PATH does not expose `pytest` or `python`. This changed verification mechanics only, not task scope or shipped behavior.

## Known Issues

`docs/hosted-reinforcement-boundary.md` still does not exist, so the full slice artifact check remains expectedly red until T03 creates it.

## Files Created/Modified

- `console/src/components/hosted/trust-boundary-card.tsx` — now renders shared operator guidance, reinforcement guardrails, and bounded-action phrasing from the canonical hosted contract.
- `console/src/components/hosted/trust-boundary-card.test.tsx` — locks the new card sections and shared non-authoritative phrasing.
- `console/src/app/trust-boundary/page.tsx` — now composes its public trust-boundary narrative from shared hosted-contract claims and guardrails instead of local restatements.
- `console/src/app/trust-boundary/page.test.tsx` — verifies the shared page/card narrative and tolerates intentional duplicate phrase reuse.
- `.gsd/milestones/M004/slices/S01/S01-PLAN.md` — marks T02 complete.
