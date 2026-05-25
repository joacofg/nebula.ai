# Research — S05: Integrated resilience proof

## Summary
S05 is light-to-targeted research. The hard technical work is already done in S02–S04; this slice is an assembly slice that should produce one bounded, pointer-first integrated proof for M010 rather than new runtime behavior. It directly supports R086 and R089, and indirectly closes R088 by showing the operator-visible inspection path in the same review order as outage and recovery truth. The main risk is not missing code paths; it is proof sprawl: duplicating contracts, inventing a new dashboard/runbook product, or letting hosted/operator surfaces outrank local runtime truth.

Memory check reinforced the existing pattern: MEM038 says close-out proof should be pointer-only and discoverable from canonical docs rather than restating contracts inline. That fits this slice exactly.

## Active requirements this slice owns/supports
- **R086** — final integrated resilience proof showing outage trigger, degraded runtime truth, operator inspection, and recovery confirmation in one reviewable path.
- **R088** — supported by including the existing console runtime-health and Observability seams in the review order, but not by adding new UI work.
- **R089** — supported by folding the verified S04 recovery path into the final milestone walkthrough.

## Recommendation
Treat S05 as a **docs/discoverability assembly slice**, not a backend or console feature slice.

Best path:
1. Create a new integrated-proof doc under `docs/` for M010 that follows the M006/M009 pointer-first pattern.
2. Make that doc subordinate to the already-written `docs/m010-recovery-proof.md` rather than replacing it.
3. Add discoverability links from repo entry docs so reviewers can actually find the M010 proof path.
4. Reuse existing executable seams as evidence only; do not add new resilience endpoints, new outage fixtures, or a new dashboard.

First proof should be the integrated doc itself, because the biggest failure mode is architectural/documentation drift, not code correctness.

## Implementation landscape

### Existing proof inputs already available
- `docs/m010-recovery-proof.md`
  - Already provides the bounded recovery walkthrough and canonical runtime truth ordering.
  - S05 should depend on it instead of re-explaining recovery mechanics in full.
- `tests/test_phase10_outage_safety.py`
  - Already proves both outage classes and recovery transitions needed by S05:
    - governance fail-closed outage
    - semantic-cache degraded-serving outage
    - governance recovery back to ready serving
    - semantic-cache degraded → recovering → ready
- `tests/test_health.py`
  - Already locks readiness/dependency semantics for degraded, recovering, and serving-critical cases.
- `console/e2e/observability.spec.ts`
  - Already contains a request-first operator inspection scenario with governance, semantic-cache, and recovering premium-provider examples.
  - Important caveat from S03 summary: this Playwright proof file exists but execution is blocked by a pre-existing unrelated console build/type issue, so S05 should not depend on fresh browser execution unless planner explicitly adds blocker work.

### Existing documentation pattern to copy
- `docs/m009-integrated-proof.md`
  - Best structural template for S05.
  - Pattern is: define canonical sources, explain what the integrated proof establishes, enforce a strict proof order, include minimal operator walkthrough, list anti-duplication boundaries, and end with failure modes.
- `docs/m006-integrated-proof.md`, `docs/m007-integrated-proof.md`, `docs/m008-integrated-proof.md`
  - Confirm this repo’s close-out convention: integrated proof docs are discoverability/pointer layers, not full contracts.

### Discoverability surfaces likely needing updates
- `README.md`
  - Documentation map currently lists integrated proofs through M009 and other proof docs, but nothing for M010 yet.
  - Likely needs one bullet for the M010 integrated resilience proof.
- `docs/architecture.md`
  - Has a long paragraph of milestone-proof links through M009.
  - Likely needs one sentence/link for the M010 integrated resilience proof so the architecture page remains the proof index.

## Files and purpose
- `docs/m010-integrated-proof.md` **(new)**
  - Primary deliverable. Assemble outage trigger, health truth, serving consequence, operator corroboration, and recovery confirmation into one pointer-first path.
- `README.md`
  - Add discoverability link in the documentation/proof map.
- `docs/architecture.md`
  - Add one bounded reference to the new integrated proof in the milestone proof chain.

Optional-but-only-if-planner-wants-extra-proofing:
- `docs/m010-recovery-proof.md`
  - Only touch if cross-links are missing; avoid substantive rewrite.

## Natural seams
1. **Integrated proof document authoring**
   - Independent, highest-value seam.
   - Produces the canonical M010 close-out walkthrough.
2. **Discoverability links**
   - Small follow-up seam in `README.md` and `docs/architecture.md`.
   - Can be done after the doc exists.
3. **Optional cross-link cleanup**
   - Only if planner sees a gap between the new integrated doc and `docs/m010-recovery-proof.md`.

These seams are nearly independent; only the discoverability step depends on the final doc path/title.

## What the integrated proof should say
The planner should preserve these boundaries from milestone context and prior slices:
- Start from **local authority** and existing health surfaces first.
- Use `/health/ready` and `/health/dependencies` as the first truth seam for outage classification.
- Show both outage classes in one joined story:
  - governance store = serving-critical, fail-closed
  - semantic cache = serving-optional, continuity-limited
- Use existing serving-path evidence from `tests/test_phase10_outage_safety.py` to show runtime consequence.
- Use existing console surfaces as corroboration only:
  - `console/src/app/(console)/observability/page.tsx`
  - `console/src/components/health/runtime-health-cards.tsx`
- Fold in recovery confirmation by pointing to `docs/m010-recovery-proof.md` and the recovery tests rather than duplicating their full detail.
- Explicitly preserve anti-sprawl boundaries:
  - no new resilience dashboard
  - no new resilience API family
  - no hosted-authoritative health/recovery story
  - no chaos-platform implication

## First proof
**Write the integrated doc first.**

Why this is the highest-risk seam:
- The engineering proof already exists across S02–S04.
- The remaining milestone risk is that the final close-out either duplicates too much, misses a canonical source, or weakens the trust boundary by making console/hosted surfaces look authoritative.
- A good integrated doc gives the planner a stable center for any tiny follow-up edits.

## Constraints and watch-outs
- Do **not** widen `docs/m010-integrated-proof.md` into a second recovery runbook; `docs/m010-recovery-proof.md` already owns the recovery-detail walkthrough.
- Do **not** restate resilience field contracts in full if they already live on shipped runtime surfaces/tests.
- Do **not** require fresh Playwright execution for completion unless the unrelated console blocker is explicitly taken on.
- Keep the selected-request-first/operator-surface wording consistent with S03; dependency health is supporting context, not a replacement for request evidence.
- Keep hosted wording subordinate to `docs/hosted-reinforcement-boundary.md` and the milestone context’s local-authority rule.

## Suggested structure for `docs/m010-integrated-proof.md`
Mirror M009’s sections with M010-specific content:
1. Title + purpose
2. Canonical sources and their roles
3. What this integrated proof establishes
4. Canonical proof order
   - trust boundary / scope
   - outage truth on health surfaces
   - governance fail-closed serving consequence
   - semantic-cache degraded-serving consequence
   - operator corroboration on existing console surfaces
   - recovery confirmation via same health surfaces + recovery proof doc/tests
   - executable anti-drift seams
5. How the sources fit together (table)
6. Minimal reviewer/operator walkthrough
7. What this walkthrough intentionally does not duplicate/add
8. Failure modes this integrated proof makes obvious
9. Related docs and code-backed seams

## Verification
Primary verification should stay lightweight and truthful for a docs assembly slice:
- `python3 -c "from pathlib import Path; p = Path('docs/m010-integrated-proof.md'); assert p.exists() and p.stat().st_size > 0; print(p.stat().st_size)"`
- `rg -n "m010-integrated-proof" README.md docs/architecture.md docs/m010-recovery-proof.md docs/m010-integrated-proof.md`

Useful evidence references (already proven; no need to expand unless planner chooses):
- `.venv/bin/pytest tests/test_phase10_outage_safety.py tests/test_health.py -q`
- `npm --prefix console run test -- --run src/components/health/runtime-health-cards.test.tsx 'src/app/(console)/observability/page.test.tsx' 'src/app/(console)/observability/observability-page.test.tsx'`

Do not make Playwright the required proof unless the unrelated console blocker is addressed.

## Skill notes
Installed skills already cover the relevant style/discipline:
- **write-docs** — directly relevant for the new integrated proof doc; use its stranger-readable, pointer-first discipline.
- **observability** — relevant for preserving runtime truth hierarchy and existing-surface discipline.

I attempted external skill discovery for FastAPI/Next.js/Playwright via `npx skills find`, but the research-slice tools policy blocks non-read-only bash execution in this unit, so no additional skill inventory could be gathered here.

## Planner-ready task split
- **T01:** Author `docs/m010-integrated-proof.md` from existing S02/S03/S04 proof seams using the M009 template pattern.
- **T02:** Add discoverability links in `README.md` and `docs/architecture.md`; optionally add a small cross-link from `docs/m010-recovery-proof.md` if needed.

That should be enough to complete S05 without reopening backend or console implementation work.