# S01: Hosted reinforcement boundary

**Goal:** Lock the hosted reinforcement vocabulary, trust-boundary guardrails, and non-authoritative wording into the shared hosted-contract seam so downstream fleet-posture work can improve clarity without implying hosted serving-time or policy authority.
**Demo:** The console exposes one canonical hosted reinforcement language contract across the shared content module, public trust-boundary surfaces, and deployment-facing bounded-action copy, with focused tests and a reusable slice artifact proving hosted summaries remain metadata-backed and descriptive only.

## Must-Haves

- R034 is advanced by centralizing explicit allowed hosted posture vocabulary and explicit prohibited authority implications in the existing `console/src/lib/hosted-contract.ts` seam, with tests that fail on drift.
- R014 is partially advanced by wiring the same guardrails into the public trust-boundary and deployment-facing console surfaces so hosted reinforcement grows only where it materially improves onboarding clarity and operator confidence.
- Deployment-facing hosted action wording stays bounded to the existing audited credential-rotation model and does not imply broader remote control, serving-time health authority, routing authority, fallback authority, or policy authority.
- A reusable slice artifact captures the reinforcement rules and downstream acceptance criteria S02/S03 must preserve.

## Proof Level

- This slice proves: contract
- Real runtime required: no
- Human/UAT required: no

## Verification

- `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx src/components/deployments/remote-action-card.test.tsx`
- `pytest tests/test_hosted_contract.py tests/test_remote_management_api.py -q`
- `rg -n "metadata-only|request-serving path|local runtime authority|serving traffic|tenant policy|provider credentials|fleet posture|confidence" console/src docs`
- `test -f docs/hosted-reinforcement-boundary.md`

## Observability / Diagnostics

- Runtime signals: Vitest assertion failures on shared copy drift and component render drift; pytest failures on hosted-contract and remote-action guardrails
- Inspection surfaces: `console/src/lib/hosted-contract.ts`, the four focused frontend test files, backend contract tests, and `docs/hosted-reinforcement-boundary.md`
- Failure visibility: exact failing copy assertion, missing rendered section, or grep-visible wording mismatch across console/doc surfaces
- Redaction constraints: preserve the metadata-only hosted contract; no raw prompts, responses, credentials, tenant secrets, or authoritative runtime policy state may be implied or newly exposed

## Integration Closure

- Upstream surfaces consumed: `console/src/lib/hosted-contract.ts`, `console/src/components/hosted/trust-boundary-card.tsx`, `console/src/app/trust-boundary/page.tsx`, `console/src/components/deployments/remote-action-card.tsx`, `tests/test_hosted_contract.py`, `tests/test_remote_management_api.py`
- New wiring introduced in this slice: shared reinforcement vocabulary exported from the hosted-contract module and reused by public trust-boundary plus deployment-facing bounded-action surfaces
- What remains before the milestone is truly usable end-to-end: S02 must build the real fleet posture reading layer on top of these guardrails, and S03 must assemble the integrated confidence proof

## Tasks

- [ ] **T01: Lock shared hosted reinforcement guardrails in the canonical content module** `est:45m`
  - Why: S01 succeeds or fails on preventing vocabulary drift. The safest move is to extend the existing schema-backed `hosted-contract.ts` seam rather than create new local copy islands.
  - Files: `console/src/lib/hosted-contract.ts`, `console/src/lib/hosted-contract.test.ts`
  - Do: Add structured reinforcement vocabulary and trust-boundary guardrails to the shared hosted contract module, including allowed descriptive framing, explicit non-authority claims to avoid, and bounded-action wording hooks that downstream UI can consume; extend focused tests to lock the new exports and keep schema/copy parity strict.
  - Verify: `npm --prefix console run test -- --run src/lib/hosted-contract.test.ts`
  - Done when: The hosted contract module is the single source of truth for reinforcement vocabulary/guardrails and its tests fail if downstream copy would drift from the metadata-only, non-authoritative boundary.
- [ ] **T02: Render the canonical trust-boundary guardrails on hosted public surfaces** `est:45m`
  - Why: The milestone needs one canonical narrative surface that downstream slices and proof artifacts can cite, not just an internal content module.
  - Files: `console/src/components/hosted/trust-boundary-card.tsx`, `console/src/components/hosted/trust-boundary-card.test.tsx`, `console/src/app/trust-boundary/page.tsx`, `console/src/app/trust-boundary/page.test.tsx`
  - Do: Reuse the shared hosted-contract exports to present the reinforcement guardrails and operator-reading guidance on the trust-boundary card and public trust-boundary page, keeping the message descriptive and explicitly non-authoritative; add or update focused render assertions for the new sections and wording.
  - Verify: `npm --prefix console run test -- --run src/components/hosted/trust-boundary-card.test.tsx src/app/trust-boundary/page.test.tsx`
  - Done when: A reader can open the public trust-boundary surfaces and see the canonical reinforcement framing, freshness caveat, and non-authority guardrails without conflicting local wording.
- [ ] **T03: Align deployment-facing hosted action copy and publish the slice boundary artifact** `est:1h`
  - Why: S01 must close the loop where hosted authority drift is most likely to reappear: deployment management copy and downstream planning handoff.
  - Files: `console/src/components/deployments/remote-action-card.tsx`, `console/src/components/deployments/remote-action-card.test.tsx`, `console/src/app/(console)/deployments/page.tsx`, `docs/hosted-reinforcement-boundary.md`
  - Do: Replace deployment-facing hosted wording that could drift with phrasing sourced from the shared hosted contract, keeping remote actions explicitly bounded to audited credential rotation and visibility-only semantics; add a concise slice artifact documenting allowed hosted claims, prohibited authority implications, and acceptance rules for S02/S03.
  - Verify: `npm --prefix console run test -- --run src/components/deployments/remote-action-card.test.tsx && rg -n "metadata-only|request-serving path|local runtime authority|serving traffic|tenant policy|provider credentials|fleet posture|confidence" console/src docs && test -f docs/hosted-reinforcement-boundary.md`
  - Done when: Deployment-facing copy matches the shared trust-boundary language, no broader hosted-control implication is introduced, and downstream slices have a concrete doc artifact to consume.

## Files Likely Touched

- `console/src/lib/hosted-contract.ts`
- `console/src/lib/hosted-contract.test.ts`
- `console/src/components/hosted/trust-boundary-card.tsx`
- `console/src/components/hosted/trust-boundary-card.test.tsx`
- `console/src/app/trust-boundary/page.tsx`
- `console/src/app/trust-boundary/page.test.tsx`
- `console/src/components/deployments/remote-action-card.tsx`
- `console/src/components/deployments/remote-action-card.test.tsx`
- `console/src/app/(console)/deployments/page.tsx`
- `docs/hosted-reinforcement-boundary.md`
