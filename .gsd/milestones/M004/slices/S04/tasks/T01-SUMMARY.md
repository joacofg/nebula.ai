---
id: T01
parent: S04
milestone: M004
provides:
  - Tightened shared hosted wording and aligned the deployments drawer/action seam to the descriptive-only contract.
key_files:
  - console/src/lib/hosted-contract.ts
  - console/src/components/deployments/deployment-detail-drawer.tsx
  - console/src/components/deployments/remote-action-card.tsx
  - console/src/lib/hosted-contract.test.ts
  - console/src/app/(console)/deployments/page.test.tsx
  - console/src/components/deployments/remote-action-card.test.tsx
key_decisions:
  - Reused shared hosted-contract guidance for drawer-level evidence framing instead of inventing page-local trust copy.
patterns_established:
  - Treat drawer freshness/dependency details as supporting evidence for fleet posture, with all trust-boundary wording sourced from hosted-contract exports.
observability_surfaces:
  - console/src/lib/hosted-contract.ts; console/src/components/deployments/deployment-detail-drawer.tsx; console/src/components/deployments/remote-action-card.tsx; focused Vitest assertions
duration: 1h
verification_result: passed
completed_at: 2026-03-24T12:23:00-03:00
blocker_discovered: false
---

# T01: Tighten shared hosted wording and the narrowest UI seam

**Tightened hosted contract guidance and reused it in the deployments drawer/action seam so the console reads as descriptive-only without page-local authority drift.**

## What Happened

I compared the public trust-boundary page, deployments page, summary/table surfaces, drawer, and remote-action card to find the smallest real wording gap. The gap was at the drawer/action seam: the shared contract already framed fleet posture as metadata-backed, but the drawer only exposed raw freshness plus bespoke caution text.

I extended `console/src/lib/hosted-contract.ts` with one additional canonical operator-reading guidance line that explicitly treats drawer-level freshness and dependency details as supporting evidence for fleet posture rather than hosted runtime authority. I then reused that shared wording in `console/src/components/deployments/deployment-detail-drawer.tsx` and `console/src/components/deployments/remote-action-card.tsx`.

I updated the nearest focused tests so wording drift now fails at the shared contract seam and at the joined deployments walkthrough seam. I also added a knowledge entry for the Vitest parenthesized-path gotcha encountered during verification.

## Verification

I ran the focused hosted-contract and deployments-console Vitest checks plus the required wording grep. The focused Vitest set passed after the drawer fix, and the grep confirmed the expected trust-boundary vocabulary remains present across `console/src`.

I also attempted direct single-file Vitest invocations for the parenthesized `src/app/(console)/...` path and for isolated summary/page files. Those failed due to Vitest/shell pattern handling rather than product behavior, so I recorded that as knowledge instead of treating it as a feature regression.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx` | 0 | ✅ pass | 1.04s |
| 2 | `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx 'src/app/(console)/deployments/page.test.tsx'` | 0 | ✅ pass | 1.06s |
| 3 | `rg -n "metadata-backed and descriptive only|local runtime authority|request-serving path|fleet posture|bounded operational assistance|credential rotation|stale|offline" console/src` | 0 | ✅ pass | 3.8s |
| 4 | `npm --prefix console run test -- --run 'src/components/deployments/fleet-posture-summary.test.tsx'` | 1 | ❌ fail | 7.2s |
| 5 | `npm --prefix console run test -- --run 'src/app/\(console\)/deployments/page.test.tsx'` | 1 | ❌ fail | 3.3s |

## Diagnostics

Inspect `console/src/lib/hosted-contract.ts` for the canonical descriptive-only wording, then inspect `console/src/components/deployments/deployment-detail-drawer.tsx` and `console/src/components/deployments/remote-action-card.tsx` to confirm those surfaces only reuse shared contract language. Focused failures should localize whether drift happened in the shared wording seam or in the deployments composition seam.

## Deviations

None in shipped scope. The only adaptation was verification handling: direct Vitest targeting of parenthesized app paths was unreliable from the repo-root command form, so I relied on the focused aggregate run and documented the gotcha.

## Known Issues

Direct `vitest --run` targeting for files under `src/app/(console)/...` can fail because of shell/Vitest pattern handling even when the file exists and aggregate focused runs pass.

## Files Created/Modified

- `console/src/lib/hosted-contract.ts` — added canonical drawer-level evidence guidance to the shared hosted contract.
- `console/src/components/deployments/deployment-detail-drawer.tsx` — surfaced posture detail plus shared supporting-evidence guidance in the freshness section.
- `console/src/components/deployments/remote-action-card.tsx` — replaced bespoke caution copy with reused shared contract guidance.
- `console/src/lib/hosted-contract.test.ts` — locked the added guidance and shared contract expectations.
- `console/src/app/(console)/deployments/page.test.tsx` — asserted the joined deployments walkthrough reuses the shared contract wording.
- `console/src/components/deployments/remote-action-card.test.tsx` — asserted the bounded-action surface reuses the shared descriptive-only wording.
- `.gsd/KNOWLEDGE.md` — recorded the Vitest parenthesized-path verification gotcha.
