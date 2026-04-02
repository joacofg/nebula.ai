# S05 Research — Integrated proof and close-out

## Summary
- **Primary requirement:** `R039` remains active and this slice is the close-out proof slice for it. S05 supports the milestone’s final acceptance criteria more than it introduces new runtime behavior.
- This is **light-to-targeted research**. The calibrated routing contract, ledger-backed calibration summary, runtime/simulation parity, and operator inspection surfaces already exist from S01–S04. The missing work is to **assemble one integrated M006 proof path** and verify the assembled worktree still tells the same calibrated-routing story end to end.
- The repo already has two strong precedents for this pattern:
  - `docs/integrated-adoption-proof.md` for the original chat adoption story
  - `docs/v4-integrated-proof.md` for pointer-only decisioning close-out in M005
- S05 should stay **pointer-only and composition-first**. Do not redefine route vocabulary, simulation response shapes, or console behavior in a new long-form contract. Point back to the canonical sources and prove they agree.

## Recommendation
Plan S05 as a **final assembly slice**, not another architecture slice.

1. **Add one M006-specific integrated proof artifact** under `docs/`.
   - Mirror the shape of `docs/v4-integrated-proof.md` and `docs/embeddings-integrated-adoption-proof.md`.
   - Keep it pointer-only.
   - The proof order should stay explicit:
     1. stable route vocabulary (`docs/route-decision-vocabulary.md`)
     2. one real public `POST /v1/chat/completions`
     3. public `X-Request-ID` + `X-Nebula-*` headers, including calibrated route metadata
     4. `GET /v1/admin/usage/ledger?request_id=...`
     5. policy simulation replay for the same tenant traffic class
     6. selected-request-first Observability / request detail corroboration
     7. bounded rollout-disabled / degraded semantics and milestone scope guardrails
2. **Update discoverability surfaces only as pointers**.
   - `README.md`
   - `docs/architecture.md`
   - Do not duplicate route-score, route-mode, or simulation semantics there.
3. **Use focused verification to prove assembled agreement**.
   - Backend tests already exist for live runtime evidence, replay parity, and admin surfaces.
   - Console tests already exist for request-detail and Observability rendering.
   - S05 likely needs one small integrated verification seam or a close-out-focused test extension, but should prefer extending existing tests over inventing a new harness.

## Implementation Landscape

### Canonical sources already in place
- `docs/route-decision-vocabulary.md`
  - Canonical vocabulary for `route_mode`, calibrated/degraded semantics, additive score components, and reason codes.
  - This should be the first proof seam in any M006 integrated doc.
- `src/nebula/api/routes/chat.py`
  - Public `POST /v1/chat/completions` path still emits `X-Request-ID` and `X-Nebula-*` headers via `_nebula_headers(...)`.
  - S01 already locked route-score / route-mode propagation into this path.
- `src/nebula/api/routes/admin.py`
  - Existing admin seams needed for S05 are already present:
    - `GET /v1/admin/usage/ledger`
    - `POST /v1/admin/tenants/{tenant_id}/policy/simulate`
    - `GET /v1/admin/tenants/{tenant_id}/recommendations`
  - No new admin API family is needed for close-out.
- `src/nebula/models/governance.py`
  - Contains the typed operator-facing proof shapes already needed by S05:
    - `UsageLedgerRecord`
    - `CalibrationEvidenceSummary`
    - `PolicySimulationChangedRequest`
    - `PolicySimulationResponse`
    - `RecommendationBundle`
- `src/nebula/services/policy_simulation_service.py`
  - Already encodes the replay contract S05 needs to cite and verify:
    - newest-fetched rows replayed oldest-first
    - changed requests sampled from that deterministic order
    - baseline/simulated route parity derived from persisted ledger signals and route decisions
    - shared `calibration_summary` included in replay output
- `console/src/components/ledger/ledger-request-detail.tsx`
  - Selected-row authoritative proof surface.
  - Already renders calibration evidence, routing inspection, budget evidence, and route signals from persisted row data.
- `console/src/app/(console)/observability/page.tsx`
  - Already frames the page as **selected request evidence first**, with calibration summary, recommendations, cache posture, and dependency health as supporting context.
- `console/src/components/policy/policy-form.tsx`
  - Already renders compact replay parity lines for changed-request samples:
    - calibrated → degraded
    - degraded → rollout disabled
  - Good reference if S05 needs one integrated wording/test seam.

### Existing test seams S05 should reuse
- `tests/test_response_headers.py`
  - Locks `X-Nebula-Route-Mode`, `X-Nebula-Route-Score`, and correlated route signals on public responses.
  - This is the public-header proof seam.
- `tests/test_governance_api.py`
  - Already contains runtime-to-replay parity coverage for calibrated, degraded, and rollout-disabled cases using real runtime requests plus correlated ledger rows.
  - This is the strongest existing integrated backend seam for S05.
- `tests/test_service_flows.py`
  - Already tests calibration summary classification, policy simulation semantics, replay parity fields, and deterministic changed-request ordering.
  - Best place for any small service-level close-out assertion if needed.
- `console/src/components/ledger/ledger-request-detail.test.tsx`
  - Locks calibrated, degraded, rollout-disabled, and unscored request-detail rendering.
- `console/src/app/(console)/observability/observability-page.test.tsx`
  - Locks selected-request-first Observability framing and bounded supporting context.
- `console/src/app/(console)/observability/page.test.tsx`
  - Locks page-level framing.
- `console/src/components/policy/policy-page.test.tsx`
  - Locks compact replay parity wording in preview cards.

### Existing close-out precedent to follow
- `docs/v4-integrated-proof.md`
  - Best structural precedent for M006.
  - Pointer-only, canonical-source map, explicit proof order, “what this does not duplicate”, and “failure modes this proof makes obvious”.
- `docs/embeddings-integrated-adoption-proof.md`
  - Best precedent for how a narrow public-response → header → ledger → Observability integrated doc should read without becoming a second contract.

## Natural task seams

### Task seam 1 — integrated M006 proof document
**Primary files**
- new `docs/<m006-integrated-proof>.md`
- possibly `README.md`
- possibly `docs/architecture.md`

**Goal**
Create one pointer-only walkthrough that assembles the calibrated-routing story end to end without redefining any existing contract.

**What it should cover**
- what the proof establishes
- canonical proof order
- how the canonical sources fit together
- minimal operator/reviewer walkthrough
- what the walkthrough intentionally does not duplicate
- failure modes that make scope drift obvious

**What it should point to**
- `docs/route-decision-vocabulary.md`
- public `POST /v1/chat/completions` path and response-header evidence
- `GET /v1/admin/usage/ledger?request_id=...`
- `POST /v1/admin/tenants/{tenant_id}/policy/simulate`
- `console/src/components/policy/policy-form.tsx`
- `console/src/app/(console)/observability/page.tsx`
- existing tests as executable proof seams where appropriate

**Risk**
Low. Mostly document composition discipline.

### Task seam 2 — focused proof/discoverability verification
**Primary files**
- `tests/test_governance_api.py`
- `tests/test_response_headers.py`
- maybe `tests/test_service_flows.py`
- maybe `console/src/app/(console)/observability/page.test.tsx`
- maybe `console/src/components/policy/policy-page.test.tsx`

**Goal**
Confirm the assembled proof path is still executable and coherent in the current worktree.

**Likely implementation details**
- Prefer extending an existing focused test rather than adding a new integration harness.
- Candidate close-out seam:
  - one backend test that explicitly walks public request headers → request_id ledger correlation → simulation parity fields for a calibrated/degraded/gated scenario.
- Candidate console seam:
  - only if needed, tighten wording assertions so Observability and policy preview still preserve the integrated order and bounded roles.

**Risk**
Low-medium. The main risk is overreaching into a broad new test instead of extending the strongest existing ones.

### Task seam 3 — requirement / close-out evidence update
**Primary files**
- `.gsd/REQUIREMENTS.md` update will happen at slice completion, not in this slice’s implementation work itself
- `.gsd/KNOWLEDGE.md` only if a new close-out rule is learned

**Goal**
Capture whether the assembled proof is now strong enough to validate `R039`, or whether it only advances it further.

**Important constraint**
Do not flip `R039` to validated unless the assembled proof demonstrates the full stronger claim: calibrated live routing, replay parity, degraded/rollout-disabled behavior, operator inspection closure, and anti-sprawl discipline together in the final worktree.

## Constraints and guardrails
- From the preloaded knowledge and prior slices:
  - Keep the integrated walkthrough **composition-first and pointer-only**.
  - The selected persisted ledger row remains the authoritative operator proof surface.
  - Replay parity proof should continue to start from a **real runtime request plus correlated usage-ledger row**, not a synthetic-only replay fixture.
  - `route_mode=null` remains an intentional state for rollout-disabled or policy-forced routing.
  - Duplicate calibration labels across bounded cards are acceptable; tests must scope with `within(...)` instead of forcing uniqueness.
- From the loaded `react-best-practices` skill:
  - Keep React/Next changes local and explicit.
  - Avoid speculative abstraction if only wording/assertion reuse is needed.
- Scope discipline from the milestone context:
  - no new admin API family
  - no analytics-style dashboard
  - no hidden weighting or black-box optimization framing
  - no hosted-authority drift
  - no public API expansion

## What to build or prove first
1. **First:** create the integrated proof document.
   - This is the clearest missing artifact compared with M005 and earlier integrated close-outs.
2. **Second:** wire discoverability pointers.
   - README and architecture should help reviewers find the proof, but only by linking.
3. **Third:** re-run/extend focused proof seams.
   - Backend first, because that is the strongest integrated evidence.
   - Console second, only if the doc or final framing exposes wording drift.
4. **Last:** use slice completion to decide requirement status based on the actual assembled evidence.

## Verification
Prefer the focused existing suites and file/link checks.

### Backend proof checks
```bash
./.venv/bin/pytest tests/test_response_headers.py -x
./.venv/bin/pytest tests/test_governance_api.py -k "simulation and calibrated" -x
./.venv/bin/pytest tests/test_service_flows.py -k "calibration_summary or simulation" -x
```

### Console proof checks
```bash
npm --prefix console run test -- --run src/components/ledger/ledger-request-detail.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/app/'(console)'/observability/page.test.tsx src/components/policy/policy-page.test.tsx
```

### Discoverability / integrated-doc checks
Assuming a new M006 proof doc is added:
```bash
rg -n "route-decision-vocabulary|X-Request-ID|X-Nebula-|/v1/admin/usage/ledger|policy/simulate|Observability|does not duplicate|failure modes" README.md docs/architecture.md docs/*.md
```

### Close-out integrity check
Use the correct integration-base branch from milestone metadata before marking the milestone complete; do not compare only to `main`.

## Skill discovery
Installed relevant skill already available:
- `react-best-practices` — enough for any small console wording/assertion adjustments.

Promising external skills, not installed:
- `wshobson/agents@fastapi-templates` — install with `npx skills add wshobson/agents@fastapi-templates`
  - Highest-install FastAPI skill surfaced by `npx skills find "FastAPI"`; relevant only if close-out unexpectedly needs API/test refactoring.
- `wshobson/agents@nextjs-app-router-patterns` — install with `npx skills add wshobson/agents@nextjs-app-router-patterns`
  - Highest-install Next.js skill surfaced by `npx skills find "Next.js"`; relevant only if console close-out work grows beyond small local edits.

## Files the planner should expect to touch
Most likely:
- `docs/<new-m006-integrated-proof>.md`
- `README.md`
- `docs/architecture.md`
- `tests/test_governance_api.py`
- `tests/test_response_headers.py`

Possible but optional:
- `tests/test_service_flows.py`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`

## Bottom line
S05 should be planned as **integrated proof assembly plus focused re-verification**. The calibrated-routing runtime, replay, and operator surfaces are already built. The missing work is to make the final review path discoverable, keep it pointer-only, and prove the assembled worktree still shows one coherent story: public calibrated evidence, correlated ledger truth, replay parity, bounded degraded/rollout-disabled semantics, and selected-request-first operator inspection without analytics or black-box drift.
