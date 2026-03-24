# S04: Targeted reinforcement refinements — Research

## Summary
S04 owns the close-out guardrail work for the still-active requirements in this milestone: **R034** as the primary ongoing constraint, plus **R014** as milestone-level support. R037/R038 were validated in S03, so this slice should not create new proof surfaces or broaden scope; it should only tighten wording, evidence mapping, and interpretation gaps revealed by the now-canonical hosted walkthrough.

This is a **light research** slice. The codebase already has the main seams in place: `console/src/lib/hosted-contract.ts` is the wording authority, `console/src/components/deployments/fleet-posture.ts` is the posture-derivation authority, `docs/hosted-integrated-adoption-proof.md` is the canonical proof artifact, and the trust-boundary/deployments tests already assert the cross-surface story. S04 should therefore behave like a refinement pass over those seams, not a new feature slice.

## Recommendation
Treat S04 as a **targeted consistency-and-gap-closure pass**:
1. Start from the S03 integrated proof and identify any remaining wording or evidence-mapping gaps between the public trust-boundary page, deployments summary/table, detail drawer, remote-action card, and the proof doc.
2. Prefer fixing those gaps by reusing or slightly expanding `console/src/lib/hosted-contract.ts` exports rather than adding page-local prose.
3. Keep UI changes small and compositional. If a gap is in interpretation, patch the nearest existing seam instead of adding new cards, columns, or workflows.
4. Re-run the exact S03 verification bar after changes. S04 is done only if refinements preserve the existing proof while improving clarity.

Relevant skill guidance:
- Installed skill **`react-best-practices`** applies as a guardrail for console work: keep changes additive, reuse existing query/data seams, and avoid introducing new client-side fetch paths or duplicate state for what is fundamentally wording/composition work.
- Promising external skill if the team wants extra Next.js-specific review depth: `npx skills add wshobson/agents@nextjs-app-router-patterns` (highest install count in `npx skills find "Next.js"`). Not required for this slice.

## Implementation Landscape
- `console/src/lib/hosted-contract.ts`
  - Canonical wording seam for all hosted trust-boundary language.
  - Already exports: allowed descriptive claims, prohibited claims, operator reading guidance, bounded-action phrasing, freshness vocabulary, and schema-backed exported-field copy.
  - Highest-leverage S04 edit point if any wording drift or missing connective copy shows up.

- `console/src/app/trust-boundary/page.tsx`
  - Public first step of the hosted proof path.
  - Already composes `reinforcement.allowedDescriptiveClaims`, `operatorReadingGuidance`, `prohibitedAuthorityClaims`, and bounded-action phrasing directly from `hosted-contract.ts`.
  - Natural place only for small composition/order refinements, not new contract language.

- `console/src/app/(console)/deployments/page.tsx`
  - Real hosted fleet entrypoint used by the proof.
  - Header currently includes a short bounded-action + non-authority framing line sourced from shared contract content.
  - Good seam for top-level evidence-mapping refinements if the page needs a clearer bridge from fleet posture to drawer/detail interpretation.

- `console/src/components/deployments/fleet-posture-summary.tsx`
  - Page-level synthesis surface for fleet posture.
  - Already states the two key descriptive claims and includes trust-boundary + bounded-action callouts.
  - Best place to close any “how should I read this summary?” gaps without expanding UI scope.

- `console/src/components/deployments/deployment-table.tsx`
  - Mixed-state scan surface referenced by S03 and by the proof doc.
  - If proof findings exposed scan-time interpretation ambiguity, this is the row-level seam to patch. Keep compact; do not turn it into a broader operations dashboard.

- `console/src/components/deployments/deployment-detail-drawer.tsx`
  - Important S04 candidate seam because it currently composes the right elements (freshness, identity, dependency summary, trust-boundary card, remote-action card) but contains very little explicit connective prose of its own.
  - If integrated proof findings said the drawer needs a clearer “context, not authority” cue, this is the most plausible place to add a small shared-contract-backed callout.

- `console/src/components/deployments/remote-action-card.tsx`
  - Already includes strong non-authority wording:
    - bounded action description from shared contract
    - explicit “metadata-backed and descriptive only” sentence
    - explicit local-runtime observability redirect
  - Best seam if the remaining gap concerns action-history interpretation or blocked/unavailable semantics.

- `docs/hosted-integrated-adoption-proof.md`
  - Canonical proof artifact from S03.
  - S04 should refine this only if the doc’s phrasing or step mapping no longer matches the real UI closely enough. Preserve composition-first behavior and keep it subordinate to `hosted-contract.ts`.

- `docs/hosted-reinforcement-boundary.md`
  - Acceptance contract from S01.
  - Use as a regression rubric; avoid growing it unless a gap truly belongs in the boundary contract rather than in UI/proof composition.

## What to Build or Prove First
1. **Gap inventory against the S03 proof path**
   - Compare these surfaces in order:
     - `console/src/app/trust-boundary/page.tsx`
     - `console/src/app/(console)/deployments/page.tsx`
     - `console/src/components/deployments/fleet-posture-summary.tsx`
     - `console/src/components/deployments/deployment-table.tsx`
     - `console/src/components/deployments/deployment-detail-drawer.tsx`
     - `console/src/components/deployments/remote-action-card.tsx`
     - `docs/hosted-integrated-adoption-proof.md`
   - Planner should look specifically for any remaining mismatch between what the doc claims an evaluator can infer and what the UI actually says on screen.

2. **Fix shared wording first**
   - If the gap is really missing canonical language, patch `console/src/lib/hosted-contract.ts` first, then thread the updated export through consumers.
   - This keeps S04 aligned with D025 and D027.

3. **Then patch the narrowest UI seam**
   - Summary-level confusion → `fleet-posture-summary.tsx`
   - Drawer-level interpretation gap → `deployment-detail-drawer.tsx`
   - Action framing gap → `remote-action-card.tsx`
   - Page-level proof bridge gap → `deployments/page.tsx`
   - Proof-doc mismatch only → `docs/hosted-integrated-adoption-proof.md`

4. **Keep tests/doc assertions synchronized**
   - Existing tests already encode the intended walkthrough. Update the closest test file for any changed wording so the proof remains executable.

## Verification
Use the exact S03 proof bar unless the planner finds a clearly narrower subset is sufficient during intermediate steps.

### Console/Vitest proof
```bash
npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx 'src/app/(console)/deployments/page.test.tsx'
```

### Browser proof
```bash
npm --prefix console run e2e -- e2e/trust-boundary.spec.ts e2e/deployments-proof.spec.ts
```

### Backend contract proof
```bash
/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q
```

### Wording / artifact drift check
```bash
rg -n "metadata-backed and descriptive only|local runtime authority|request-serving path|fleet posture|bounded operational assistance|credential rotation|stale|offline" console/src docs && test -f docs/hosted-integrated-adoption-proof.md
```

## Constraints / Risks
- **Do not reopen scope.** S04 exists to close clarity gaps, not add new hosted mechanics, statuses, or remote actions.
- **Do not create a second wording island.** If new trust-boundary text is needed, put it in `console/src/lib/hosted-contract.ts` and reuse it.
- **Most likely refinement seam is the drawer.** The summary and remote-action surfaces are already explicit; `deployment-detail-drawer.tsx` is comparatively light on connective interpretation copy even though the S03 doc treats it as a key context step.
- **Keep proof composition-first.** `docs/hosted-integrated-adoption-proof.md` should keep delegating contract language back to `hosted-contract.ts` and `docs/hosted-reinforcement-boundary.md`.
- **Known environment gotcha from S03:** if Playwright/Next reports stale compile locations after TypeScript changes, clearing `console/.next` may be required before rerunning e2e verification.
