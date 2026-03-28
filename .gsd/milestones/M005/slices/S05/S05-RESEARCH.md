# S05 Research — Integrated v4 proof

## Summary
- **Primary active requirement:** `R044` (owner: `M005/S05`). This slice is the milestone close-out proof that the assembled v4 decisioning story stays **narrow, interpretable, operator-driven, and non-expansive**. Unlike S02–S04, this slice is mostly **integration proof + docs + verification alignment**, not new backend capability.
- This is **targeted/light research**. The core v4 mechanisms already exist and are tested:
  - simulation: `POST /v1/admin/tenants/{tenant_id}/policy/simulate`
  - recommendations: `GET /v1/admin/tenants/{tenant_id}/recommendations`
  - hard-budget vocabulary and operator docs
  - Observability framing and cache controls
- The main missing work is to assemble those existing seams into one **v4 integrated proof path** analogous to prior milestone integrated-proof docs (`docs/integrated-adoption-proof.md`, `docs/embeddings-integrated-adoption-proof.md`, `docs/hosted-integrated-adoption-proof.md`) and make it discoverable from the existing docs map without duplicating lower-level contracts.
- Strongest implementation rule from prior docs patterns: **pointer-only integrated docs** should join canonical sources in sequence and define failure modes, but should not restate contracts or invent new product surfaces. This is the key way S05 can validate R044 rather than accidentally widening scope.

## Recommendation
1. Build the slice around a new **integrated v4 proof doc** in `docs/` that assembles S02 + S03 + S04 into a single operator walkthrough.
2. Keep source-of-truth details in existing canonicals (`docs/route-decision-vocabulary.md`, `docs/policy-guardrails.md`, `docs/evaluation.md`, existing policy/observability UI/tests) and use the new integrated doc only to connect them.
3. Update **discoverability surfaces** (`README.md`, likely `docs/architecture.md`, and possibly `docs/evaluation.md` if needed) so reviewers can find the joined proof path.
4. Add focused tests or doc-integrity assertions only if needed to lock discoverability / wording / scope boundaries. Prefer lightweight proof checks over new feature behavior tests.

Reference to loaded skill guidance:
- **react-best-practices** and installed `frontend-design`/`make-interfaces-feel-better` are relevant only insofar as console surfaces should stay within existing pages and not spawn new UI areas. The codebase already follows that rule in S04: recommendations render in Observability, edits stay in Policy.
- Existing integrated-proof docs demonstrate a reusable pattern: **joined narrative, explicit order, explicit failure modes, and no contract duplication**.

## Skill Discovery (suggest)
Directly relevant core technologies for this slice are already covered by installed skills:
- **Next.js / React**: installed skill `react-best-practices` already exists and is sufficient for any console wording/touch-up work.
- **Browser/UI verification**: installed skill `agent-browser` exists if the planner later wants interactive verification.

Promising external skill found (not installed):
- `wshobson/agents@nextjs-app-router-patterns` — install via `npx skills add wshobson/agents@nextjs-app-router-patterns`
  - High install count; relevant only if S05 unexpectedly requires nontrivial Next.js app-router restructuring. Current evidence suggests it is probably unnecessary.

## Implementation Landscape

### Existing proof and narrative pattern to copy
- `docs/integrated-adoption-proof.md`
  - Canonical example of a joined proof doc.
  - Pattern:
    - explain what the integrated proof establishes
    - define strict proof order
    - point back to separate canonical docs
    - include “What this walkthrough intentionally does not duplicate”
    - include “Failure modes this integrated proof makes obvious”
- `docs/embeddings-integrated-adoption-proof.md`
- `docs/hosted-integrated-adoption-proof.md`
  - Additional examples of the same pattern for narrower scopes.

Planner note: S05 should likely produce a sibling doc such as `docs/v4-integrated-proof.md` or similarly named, using the same pattern and tone.

### Existing v4 factual sources to assemble
- `docs/route-decision-vocabulary.md`
  - Canonical S01/S03 vocabulary for route signals, reason codes, and policy outcomes.
  - Important for keeping the proof interpretable rather than sounding like opaque optimization.
- `docs/policy-guardrails.md`
  - Canonical hard-vs-soft budget behavior and inspection surfaces.
  - Important for R044 because it explicitly states this is not billing/analytics scope.
- `docs/evaluation.md`
  - Canonical benchmark commands and artifact-reading story (`make benchmark`, `make benchmark-demo`).
  - Strong candidate to reference for “convincingly better than prior heuristic posture” proof, without inventing a new evaluation system.
- `README.md`
  - Current docs map does **not** yet mention a v4 integrated proof doc.
- `docs/architecture.md`
  - Current architecture doc explains request flow, operator console, trust boundary, and benchmark harness, but does **not** yet tie simulation + guardrails + recommendations into one v4 proof pointer.

### Existing backend/API seams already available
- `src/nebula/api/routes/admin.py`
  - `GET /v1/admin/tenants/{tenant_id}/recommendations`
  - `POST /v1/admin/tenants/{tenant_id}/policy/simulate`
  - `GET /v1/admin/usage/ledger`
  - `GET /v1/admin/policy/options`
  - This slice should reuse these documented seams rather than create new close-out APIs.
- `src/nebula/services/recommendation_service.py`
  - Bounded, deterministic, tenant-scoped recommendation model.
  - Key scope-control facts already encoded in implementation/tests:
    - max 3 recommendations
    - max 2 cache insights
    - evidence arrays bounded
    - grounded in ledger + runtime cache health only
- `src/nebula/models/governance.py`
  - Canonical DTO bounds for `RecommendationBundle`, `PolicySimulationResponse`, `TenantPolicy` cache knobs and hard-budget knobs.
  - Good proof inputs because the boundedness is structurally enforced here.

### Existing console proof surfaces already available
- `console/src/app/(console)/observability/page.tsx`
  - Already frames recommendations as “recent ledger-backed traffic plus supporting runtime context” and explicitly says “not black-box optimization”.
  - Shows cache summary as inspection-only and points edits back to the policy editor.
  - This language is directly useful for S05 proof writing and should probably be referenced rather than reimagined.
- `console/src/components/policy/policy-form.tsx`
  - Already keeps preview/save explicit.
  - Already groups runtime-enforced controls vs soft-budget advisory.
  - Already includes semantic-cache wording and simulation panel.
- `console/src/lib/admin-api.ts`
  - Contains shared typed contracts for simulation and recommendations; no need for ad-hoc proof payloads.
- `console/src/lib/query-keys.ts`
  - Confirms tenant recommendations are already isolated as a first-class query surface.

### Existing tests that already prove most behavior
- `tests/test_service_flows.py`
  - RecommendationService boundedness and no-mutation tests around lines ~741+.
  - Confirms deterministic ordering, bounded outputs, degraded-cache propagation, and no writes.
- `tests/test_governance_api.py`
  - Admin recommendations endpoint tests.
  - Policy simulation endpoint tests.
  - Strong existing API-level proof seam.
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/src/components/policy/policy-form.test.tsx`
- `console/src/components/policy/policy-page.test.tsx`
  - Already assert the exact R044-friendly framing:
    - recommendation guidance is grounded, read-only, non-black-box
    - cache tuning remains in policy preview/save flow
    - simulation remains preview-before-save and non-mutating
    - hard budget copy distinguishes enforced vs advisory behavior

Planner note: this means S05 likely does **not** need net-new feature tests unless discoverability/docs need locking.

## Natural Seams

### Seam 1 — Canonical integrated proof document
Likely files:
- new `docs/<v4 integrated proof>.md`

Why first:
- This is the primary slice deliverable.
- It defines how the planner/executor frame the rest of the close-out work.
- It should assemble the already-shipped facts in this order:
  1. interpretable routing vocabulary and operator evidence
  2. preview-before-save simulation against recent ledger traffic
  3. hard cumulative guardrail behavior and downgrade/deny semantics
  4. grounded recommendation + cache-tuning guidance
  5. benchmark/evaluation proof that the assembled story is better than prior heuristic posture
  6. explicit non-goals / failure modes for R044

Expected structure should mirror prior integrated docs:
- what this proof establishes
- canonical proof order
- how canonicals fit together
- minimal integrated walkthrough
- what it intentionally does not duplicate
- failure modes this proof makes obvious

### Seam 2 — Discoverability pointers
Likely files:
- `README.md`
- `docs/architecture.md`
- maybe `docs/evaluation.md`

Why second:
- Once the new canonical integrated proof doc exists, reviewers need a path to find it.
- Existing precedent: README and architecture docs link to integrated proof docs as discoverability layers, not duplicate sources.

Recommended constraint:
- Add links and one-line descriptions only.
- Do not re-explain v4 semantics in these files.

### Seam 3 — Verification and proof locking
Likely files:
- `tests/test_governance_api.py` only if doc/discoverability integrity tests already live here or nearby
- doc-oriented tests if the repo already has a pattern; otherwise rely on focused command reruns + doc existence checks

Why last:
- S05 is mostly assembled proof, so verification should confirm the shipped seams still agree.
- Avoid turning this into a broad new acceptance test matrix unless needed.

## Risks / Constraints
- **Biggest risk:** duplicating behavior/contracts across docs and unintentionally widening scope. The integrated doc must stay pointer-oriented and sequence-oriented.
- **Second risk:** implying autonomous optimization. Existing Observability copy carefully says recommendations are bounded, grounded, read-only, and not black-box. Preserve that wording style.
- **Third risk:** inventing a new “v4 dashboard” or UI page. Existing slice summaries explicitly kept work inside current Policy and Observability surfaces; S05 should preserve that.
- **Fourth risk:** overclaiming benchmark proof. `docs/evaluation.md` provides the benchmark story, but S05 should not imply a new measurement method. It should point to `make benchmark` / `make benchmark-demo` and existing artifacts as the proof path.

## What to Build or Prove First
1. **Name and draft the integrated v4 proof doc** using the existing integrated-proof pattern.
2. Ensure the doc’s joined sequence is grounded in already-shipped surfaces:
   - `policy/simulate`
   - hard budget vocabulary/docs
   - recommendations endpoint / Observability wording
   - evaluation/benchmark artifacts
3. Add discoverability links in README/architecture.
4. Re-run the focused backend + console suites already associated with S02/S03/S04 plus a lightweight doc-presence/discoverability check.

## Verification
Recommended close-out verification set:
- `./.venv/bin/pytest tests/test_service_flows.py -k "simulation or recommendation or cache or runtime_policy or budget" -x`
- `./.venv/bin/pytest tests/test_governance_api.py -k "simulation or recommendation or guardrail or policy_options or policy_denied" -x`
- `npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx`
- `test -f docs/<v4 integrated proof>.md`
- optional lightweight grep/assertion check after writing docs to confirm README and architecture point to the new file

If the executor adds a doc-integrity test, keep it narrow:
- confirm the new integrated v4 proof doc exists
- confirm `README.md` and/or `docs/architecture.md` link to it
- do not create brittle full-text snapshot tests for long markdown docs

## File Map for Planner
- `docs/integrated-adoption-proof.md` — best template for integrated proof writing style
- `docs/embeddings-integrated-adoption-proof.md` — secondary template
- `docs/hosted-integrated-adoption-proof.md` — secondary template
- `docs/route-decision-vocabulary.md` — v4 interpretable routing/operator vocabulary
- `docs/policy-guardrails.md` — hard/soft budget semantics and scope boundary
- `docs/evaluation.md` — benchmark/evaluation proof path
- `README.md` — docs map/discoverability
- `docs/architecture.md` — architecture/discoverability pointer surface
- `src/nebula/api/routes/admin.py` — real admin seams to mention in proof
- `src/nebula/services/recommendation_service.py` — bounded/read-only recommendation semantics
- `src/nebula/models/governance.py` — bounded DTO contract
- `console/src/app/(console)/observability/page.tsx` — operator framing for recommendations/cache context
- `console/src/components/policy/policy-form.tsx` — preview-before-save and runtime-enforced-control framing
- `tests/test_service_flows.py` — existing recommendation boundedness proof
- `tests/test_governance_api.py` — existing API proof for simulation/recommendations/guardrails
- `console/src/app/(console)/observability/page.test.tsx` — wording/UX proof for grounded recommendations
- `console/src/app/(console)/observability/observability-page.test.tsx` — integrated wording/UX proof
- `console/src/components/policy/policy-form.test.tsx` — preview/save, cache tuning, hard-budget framing
- `console/src/components/policy/policy-page.test.tsx` — page-level policy framing and simulation semantics
