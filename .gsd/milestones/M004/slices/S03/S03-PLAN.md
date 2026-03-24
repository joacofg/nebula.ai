# S03: Confidence proof and trust walkthrough

**Goal:** Prove, with one canonical integrated walkthrough plus focused executable verification, that Nebula’s hosted console reinforces onboarding clarity and multi-deployment understanding while remaining explicitly non-authoritative for local runtime enforcement.
**Demo:** An evaluator can follow a single hosted proof path from the public trust-boundary page into the real deployments console, read mixed fleet posture and bounded-action states in context, and see evidence that stale/offline hosted signals still do not override local runtime authority.

## Must-Haves

- Ship a canonical hosted integrated proof document under `docs/` that assembles the existing trust-boundary, deployments summary/table/drawer, and bounded-action surfaces without redefining their contracts.
- Add focused verification that locks the integrated hosted walkthrough language and evidence mapping to the shared hosted contract and fleet-posture semantics.
- Add browser-level proof for the hosted walkthrough so the real console entry flow is exercised, not just unit-rendered.
- Preserve S01/S02 guardrails: hosted remains metadata-backed and descriptive only, bounded actions stay fail-closed and narrow, and local runtime enforcement remains authoritative when hosted data is stale or offline.
- Produce requirement-grade evidence for R037 and R038 while reinforcing active requirement R034 and materially advancing milestone-level R014.

## Proof Level

- This slice proves: final-assembly
- Real runtime required: yes
- Human/UAT required: yes

## Verification

- `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx src/app/(console)/deployments/page.test.tsx`
- `npm --prefix console run e2e -- e2e/trust-boundary.spec.ts e2e/deployments-proof.spec.ts`
- `/Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q`
- `rg -n "metadata-backed and descriptive only|local runtime authority|request-serving path|fleet posture|bounded operational assistance|credential rotation|stale|offline" console/src docs && test -f docs/hosted-integrated-adoption-proof.md`

## Observability / Diagnostics

- Runtime signals: hosted freshness state, dependency summary, bounded remote-action availability, and trust-boundary wording remain the diagnostic signals for mixed fleet interpretation.
- Inspection surfaces: `console/src/lib/hosted-contract.ts`, `console/src/components/deployments/fleet-posture.ts`, `console/src/app/(console)/deployments/page.tsx`, `console/src/components/deployments/deployment-detail-drawer.tsx`, `docs/hosted-integrated-adoption-proof.md`, and `console/e2e/deployments-proof.spec.ts`.
- Failure visibility: focused Vitest failures localize wording/composition drift; Playwright failures localize entrypoint or walkthrough regressions; backend contract tests catch trust-boundary or fail-closed remote-management drift.
- Redaction constraints: proof artifacts must stay metadata-only and must not expose prompts, responses, provider credentials, tenant secrets, or authoritative local policy state.

## Integration Closure

- Upstream surfaces consumed: `console/src/lib/hosted-contract.ts`, `console/src/components/deployments/fleet-posture.ts`, `console/src/components/deployments/fleet-posture-summary.tsx`, `console/src/components/deployments/deployment-table.tsx`, `console/src/components/deployments/deployment-detail-drawer.tsx`, `console/src/components/deployments/remote-action-card.tsx`, `console/src/app/(console)/deployments/page.tsx`, `console/src/app/trust-boundary/page.tsx`, `docs/hosted-reinforcement-boundary.md`.
- New wiring introduced in this slice: canonical hosted integrated proof documentation plus explicit test and browser-proof coverage that walks the public trust-boundary page into the deployments posture surfaces and drawer-level trust/bounded-action story.
- What remains before the milestone is truly usable end-to-end: S04 should only close gaps found by this proof; no broader hosted expansion should remain necessary.

## Tasks

- [ ] **T01: Author the canonical hosted integrated proof walkthrough** `est:45m`
  - Why: S03’s primary gap is proof assembly, not missing product seams; the slice needs one discoverable artifact that joins the real hosted story without inventing new authority or duplicate contracts.
  - Files: `docs/hosted-integrated-adoption-proof.md`, `docs/hosted-reinforcement-boundary.md`, `console/src/app/trust-boundary/page.tsx`, `console/src/app/(console)/deployments/page.tsx`, `console/src/components/deployments/deployment-detail-drawer.tsx`, `console/src/components/deployments/remote-action-card.tsx`
  - Do: Write a composition-first walkthrough doc patterned after `docs/integrated-adoption-proof.md` that explicitly walks through the public trust-boundary page, deployments fleet summary, mixed-state table interpretation, detail-drawer trust boundary, dependency context, and bounded remote action framing; keep all trust language anchored to the shared hosted-contract seam and boundary doc; add or tighten links/discoverability only if needed to make the proof doc useful without duplicating canonical contract text.
  - Verify: `test -f docs/hosted-integrated-adoption-proof.md && rg -n "trust boundary|fleet posture|local runtime|bounded operational assistance|stale|offline|credential rotation" docs/hosted-integrated-adoption-proof.md docs/hosted-reinforcement-boundary.md`
  - Done when: `docs/hosted-integrated-adoption-proof.md` exists, is non-empty, and truthfully explains the integrated hosted walkthrough while explicitly preserving local runtime authority and metadata-only hosted scope.

- [ ] **T02: Lock integrated hosted trust and evidence mapping in focused tests** `est:1h`
  - Why: The walkthrough only counts as canonical proof if code-level tests lock the public page, deployments entrypoint, and drawer-level hosted evidence story to the shared trust-boundary and fleet-posture seams.
  - Files: `console/src/app/(console)/deployments/page.test.tsx`, `console/src/components/deployments/fleet-posture-summary.test.tsx`, `console/src/components/deployments/remote-action-card.test.tsx`, `console/src/app/trust-boundary/page.test.tsx`, `console/src/lib/hosted-contract.ts`, `console/src/components/deployments/fleet-posture.ts`
  - Do: Add or extend focused Vitest coverage for the deployments page composition and any missing integrated assertions so the hosted walkthrough proves summary/table/drawer/trust-boundary alignment without snapshot sprawl; prefer asserting reuse of shared wording and helper-derived mixed-state semantics over large tree snapshots; keep the slice scoped to confidence-proof composition, not new mechanics.
  - Verify: `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/app/trust-boundary/page.test.tsx src/components/hosted/trust-boundary-card.test.tsx src/components/deployments/fleet-posture.test.ts src/components/deployments/fleet-posture-summary.test.tsx src/components/deployments/deployment-table.test.tsx src/components/deployments/remote-action-card.test.tsx src/app/(console)/deployments/page.test.tsx`
  - Done when: focused tests pass and would fail if the deployments walkthrough stopped reusing hosted-contract wording, stopped surfacing mixed-fleet interpretation, or implied hosted runtime authority.

- [ ] **T03: Add browser proof for the hosted trust walkthrough** `est:1h`
  - Why: The roadmap requires an integrated proof that exercises the real console flow; browser-level evidence closes the credibility gap between isolated render tests and the hosted adoption story operators actually experience.
  - Files: `console/e2e/deployments-proof.spec.ts`, `console/e2e/trust-boundary.spec.ts`, `console/src/app/(console)/deployments/page.tsx`, `console/src/components/deployments/deployment-detail-drawer.tsx`, `docs/hosted-integrated-adoption-proof.md`
  - Do: Create a narrow Playwright walkthrough that uses mocked deployment/admin responses to open the deployments page, confirm mixed fleet posture cues, select a deployment, and assert the trust-boundary and bounded-action text in the detail drawer; keep the flow tightly aligned with the doc and existing public trust-boundary proof rather than expanding into broader dashboard coverage.
  - Verify: `npm --prefix console run e2e -- e2e/trust-boundary.spec.ts e2e/deployments-proof.spec.ts && /Users/joaquinfernandezdegamboa/Proj/nebula/.venv/bin/python -m pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q`
  - Done when: the browser proof passes against mocked mixed-deployment data and demonstrates that hosted walkthrough surfaces remain descriptive, bounded, and explicitly secondary to local runtime authority.

## Files Likely Touched

- `docs/hosted-integrated-adoption-proof.md`
- `console/src/app/(console)/deployments/page.test.tsx`
- `console/src/components/deployments/fleet-posture-summary.test.tsx`
- `console/src/components/deployments/remote-action-card.test.tsx`
- `console/src/app/trust-boundary/page.test.tsx`
- `console/e2e/deployments-proof.spec.ts`
- `console/e2e/trust-boundary.spec.ts`
