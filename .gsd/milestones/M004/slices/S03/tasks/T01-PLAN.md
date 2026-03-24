---
estimated_steps: 4
estimated_files: 4
skills_used:
  - react-best-practices
---

# T01: Author the canonical hosted integrated proof walkthrough

**Slice:** S03 — Confidence proof and trust walkthrough
**Milestone:** M004

## Description

Write the canonical hosted integrated proof artifact for M004. This task should assemble the trust-boundary and deployments-console seams that already exist into one walkthrough an evaluator can follow end to end. The doc must stay composition-first: it should point to existing canonical contracts and UI surfaces rather than redefining them, and it must keep local runtime enforcement explicit as the authoritative serving-time source even when hosted data is stale or offline.

## Steps

1. Read the existing structure and tone of `docs/integrated-adoption-proof.md`, then draft `docs/hosted-integrated-adoption-proof.md` using the same composition-first style for the hosted reinforcement story.
2. Walk through the real hosted path in order: `console/src/app/trust-boundary/page.tsx`, `console/src/app/(console)/deployments/page.tsx`, `console/src/components/deployments/fleet-posture-summary.tsx`, `console/src/components/deployments/deployment-table.tsx`, `console/src/components/deployments/deployment-detail-drawer.tsx`, and `console/src/components/deployments/remote-action-card.tsx`.
3. Anchor the walkthrough to `docs/hosted-reinforcement-boundary.md` and `console/src/lib/hosted-contract.ts`, explicitly preserving metadata-only wording, bounded hosted action scope, and the rule that local runtime observability remains the serving-time truth.
4. If discoverability is meaningfully weak, add only the smallest supporting link/reference updates needed in existing hosted docs or pages; do not create a second wording seam or duplicate detailed contract text.

## Must-Haves

- [ ] `docs/hosted-integrated-adoption-proof.md` explains the joined proof path from public trust-boundary framing to deployments summary/table/drawer and bounded action interpretation.
- [ ] The walkthrough explicitly states that stale or offline hosted signals do not change local routing, fallback, policy, or serving-time authority.
- [ ] The document reuses canonical boundaries from `docs/hosted-reinforcement-boundary.md` and `console/src/lib/hosted-contract.ts` instead of inventing page-local phrasing.

## Verification

- `test -f docs/hosted-integrated-adoption-proof.md`
- `rg -n "trust boundary|fleet posture|local runtime|request-serving path|bounded operational assistance|credential rotation|stale|offline" docs/hosted-integrated-adoption-proof.md docs/hosted-reinforcement-boundary.md`

## Inputs

- `docs/integrated-adoption-proof.md` — structural precedent for a composition-first integrated proof artifact
- `docs/hosted-reinforcement-boundary.md` — trust-boundary acceptance contract S03 must preserve
- `console/src/lib/hosted-contract.ts` — canonical hosted wording seam the walkthrough must reference implicitly or explicitly
- `console/src/app/trust-boundary/page.tsx` — public hosted trust-boundary entrypoint
- `console/src/app/(console)/deployments/page.tsx` — real hosted fleet posture entrypoint
- `console/src/components/deployments/fleet-posture-summary.tsx` — page-level hosted fleet summary surface
- `console/src/components/deployments/deployment-table.tsx` — mixed-state deployment scan surface
- `console/src/components/deployments/deployment-detail-drawer.tsx` — detail-level trust/evidence composition surface
- `console/src/components/deployments/remote-action-card.tsx` — bounded hosted action framing surface

## Expected Output

- `docs/hosted-integrated-adoption-proof.md` — canonical integrated hosted proof walkthrough for M004/S03
- `docs/hosted-reinforcement-boundary.md` — optional discoverability or cross-link adjustment if needed
- `console/src/app/trust-boundary/page.tsx` — optional link/reference touch only if required for discoverability
- `console/src/app/(console)/deployments/page.tsx` — optional link/reference touch only if required for discoverability
