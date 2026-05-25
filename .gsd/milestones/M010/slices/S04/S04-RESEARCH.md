# S04 Research — Recovery verification and runbook proof

## Summary
Targeted research. S04 is not a broad new resilience implementation slice; it is a proof-and-runbook slice that should reuse the already-shipped outage semantics from S02 and operator-visible truth surfaces from S03. Active requirements here are **R086, R088, and especially R089**: the slice must verify at least one operator recovery path end to end, proving both restored healthy behavior and trustworthy post-recovery evidence on existing runtime and console surfaces. The highest-value path is already clear from the codebase: **governance-store fail-closed outage → recovery to ready** plus a companion **semantic-cache degraded outage → recovery to ready** because those are the two outage classes already deterministically modeled in tests.

Recommendation: make S04 pointer-first and document-backed, following the same anti-sprawl style as `docs/m009-integrated-proof.md` and the loaded `write-docs`/`observability` guidance: start from existing health and Observability surfaces, prove recovery with executable tests first, then add a bounded recovery walkthrough doc that points to those seams instead of inventing a new dashboard, API, or chaos harness. First proof should be a backend recovery transition test around the S02 outages, because that is the highest-risk gap: current tests prove outage truth, but I found **no end-to-end test that proves the same dependency can recover and that health payloads/timestamps truthfully supersede stale failure state**.

## Skill Discovery
Installed skills already relevant:
- `observability` — relevant for keeping recovery proof on existing truth surfaces and emphasizing explicit failure/recovery state.
- `write-docs` — relevant for the bounded runbook / integrated proof artifact.
- `agent-browser` and `test` — relevant if planner wants browser/UAT proof after code verification.
- `react-best-practices` / `frontend-design` are not core to this slice unless UI changes become necessary.

External skill candidates worth noting only if the user wants to install more:
- FastAPI: `npx skills add wshobson/agents@fastapi-templates` (17.8K installs) or `npx skills add mindrally/skills@fastapi-python` (9.1K installs)
- Playwright: `npx skills add currents-dev/playwright-best-practices-skill@playwright-best-practices` (42.2K installs)
- Next.js: `npx skills add vercel/next.js@runtime-debug` (1.1K installs)

## Implementation Landscape

### Existing recovery-aware contract already exists
- `src/nebula/models/resilience.py`
  - Canonical additive dependency payload builder already includes `recovering`, `last_failure_at`, and `last_recovery_at`.
  - This means S04 probably does **not** need a new payload shape; it needs proof that producers and tests use these fields truthfully during recovery.
- Memory results reinforce two constraints:
  - preserve additive compatibility fields (`status`, `required`, `detail`) while using typed resilience fields.
  - runtime readiness must derive from typed resilience semantics, not ad hoc flags.

### Runtime health surfaces are already the canonical backend proof seam
- `src/nebula/main.py`
  - `/health/ready` returns 200 for `ready|degraded`, 503 for `not_ready`.
  - `/health/dependencies` returns the full readiness payload, not a narrowed dependency-only shape.
- `src/nebula/services/runtime_health_service.py`
  - Overall status flips to `not_ready` on serving-critical failures and `degraded` on `degraded|recovering` states.
  - Important nuance for planner: a dependency in `recovering` still keeps overall readiness at `degraded`, so S04 can verify an intermediate recovery state before final `ready`.

### S02 already gives deterministic outage fixtures that can be extended into recovery
- `tests/test_phase10_outage_safety.py`
  - Contains deterministic end-to-end request + readiness + dependencies proofs for:
    - governance outage fail-closed (`FailingGovernanceStore`)
    - semantic-cache degraded continuity (`FailingSemanticCacheService`)
    - hosted metadata-only outage continuity
  - Strongest seam for S04. The file already has app harness, serving stubs, and injectable dependency doubles. Best extension path is to add **stateful doubles** or swap unhealthy→recovering→ready doubles inside the same test to prove transition and post-recovery serving behavior.
- `tests/support.py`
  - `FakeCacheService` already accepts custom `health_status_payload`; can express degraded, recovering, and ready without new infrastructure.

### Health contract tests already cover isolated recovery status, but not full recovery path
- `tests/test_health.py`
  - Already has `test_readiness_reports_recovering_dependencies_as_degraded()`.
  - Gap: this is a static payload proof only. It does not prove outage → recovery → restored serving behavior or clearing/superseding incident state.

### Console/operator surfaces are already recovery-capable and should likely be reused as-is
- `console/src/lib/admin-api.ts`
  - `RuntimeHealthDependency` already carries `recovering`, `last_failure_at`, `last_recovery_at`, and other additive fields.
- `console/src/components/health/runtime-health-cards.tsx`
  - Renders dependency class, lifecycle state, serving effect, reason code, recovering, and timestamps generically from metadata.
- `console/src/app/(console)/observability/page.tsx`
  - Already frames dependency health as supporting context under the selected-request-first workflow.
- `console/e2e/observability.spec.ts`
  - Already stubs governance fail-closed, semantic-cache degraded, and premium-provider recovering examples.
  - Important watch-out from S03 summary: Playwright execution was previously blocked by an unrelated pre-existing console build/type issue outside that slice. Planner should treat Playwright as optional / follow-up verification unless that blocker is cleared.

### Existing proof-doc pattern to copy
- `docs/m009-integrated-proof.md`
  - Canonical pointer-first proof pattern: explain proof order, point to existing seams, avoid duplicating contracts.
  - S04 should likely produce a similar resilience-specific doc, not a prose-heavy operational manual.
- Existing docs inventory shows multiple `*-integrated-proof.md` files and `docs/self-hosting.md` as the canonical deployment runbook style. There is **no existing recovery proof doc for M010** yet.

## What Is Missing
1. **End-to-end recovery transition proof** for the same dependency classes already covered by S02.
   - No test currently proves governance-store outage recovery restores serving and health truth.
   - No test currently proves semantic-cache degraded state clears back to healthy after recovery.
2. **Documented operator recovery walkthrough** for the highest-value outage classes.
   - I found integrated proof docs, but no M010 recovery/runbook artifact describing the exact review order for outage evidence, recovery action, and post-recovery confirmation.
3. **Post-recovery evidence integrity proof**.
   - S04 acceptance requires more than “dependency reachable again.” It should show health surfaces either clear stale failure state or supersede it with explicit recovery metadata, and request behavior matches the recovered state.

## Natural Seams

### Seam 1 — Backend recovery transition tests (first proof)
Primary files:
- `tests/test_phase10_outage_safety.py`
- `tests/test_health.py`
- optionally `tests/support.py`

Purpose:
- Add deterministic outage→recovering→ready or outage→ready recovery tests for governance and semantic-cache paths.
- Prove request behavior and health payloads realign after recovery.

Why first:
- Highest risk and biggest unblocker. If the runtime truth does not recover cleanly, docs and UI proof are just ceremony.

Likely task shape:
- governance recovery test: fail-closed request + 503 readiness while unhealthy, then swap to healthy store and prove chat succeeds + `/health/ready` returns 200 ready + `/health/dependencies` governance payload no longer reports fail_closed/not_ready.
- semantic-cache recovery test: degraded serving during outage, then swap payload/service to ready or recovering→ready and prove dependency health updates truthfully while chat stays successful.
- focused static contract regression in `tests/test_health.py` if runtime-health aggregation around `recovering`/`ready` needs extra locking.

### Seam 2 — Recovery proof / runbook document
Primary files:
- likely new doc under `docs/` such as `docs/m010-recovery-proof.md` or `docs/m010-integrated-resilience-proof.md`
- possibly existing milestone artifacts if planner wants a pointer from `.gsd` summaries only

Purpose:
- Write a bounded operator-facing proof order: trigger outage, inspect existing health/Observability surfaces, perform recovery step, confirm post-recovery health and request truth.
- Reuse the integrated-proof structure from M009 rather than writing a sprawling runbook.

Content shape should include:
- canonical source list
- minimal proof order
- what recovery confirmation means
- explicit anti-goals: no new dashboard, no hosted authority, no hidden manual DB repair claims

### Seam 3 — Optional console/browser proof tightening
Primary files:
- `console/e2e/observability.spec.ts`
- maybe `console/src/app/(console)/observability/*.test.tsx`

Purpose:
- Only if needed, extend stubs/assertions to show a recovered/ready post-incident view or a recovery timestamp example aligned with the runbook doc.

Risk note:
- lower priority because S03 already proved console seams via Vitest, and Playwright is known-blocked by unrelated worktree issues.

## First Proof
**Governance-store recovery path** should be first.

Why this is the best first proof:
- It is the strongest trust invariant from S02: serving-critical outage must fail closed.
- S04 acceptance explicitly needs a documented recovery path for highest-value outages; governance is highest-value because it blocks safe serving and readiness.
- It exercises the hardest reconciliation question: after a fail-closed incident, does Nebula return to truthful healthy serving without stale failure claims?

Exact proof target:
1. induce deterministic governance outage in `tests/test_phase10_outage_safety.py`
2. assert `/v1/chat/completions` returns 503 with `Governance store unavailable.`
3. assert `/health/ready` is 503 `not_ready`
4. restore healthy governance store
5. assert `/v1/chat/completions` succeeds
6. assert `/health/ready` returns 200 with `ready` (or `degraded` only if another dependency is intentionally recovering)
7. assert `/health/dependencies` governance entry is truthfully healthy/recovered and no longer fail-closed/not_ready

If this fails, only then inspect backend producers for stale state bugs.

## Verification
Recommended verification ladder for planner:

### Backend must-pass
- `.venv/bin/pytest tests/test_phase10_outage_safety.py -q`
- `.venv/bin/pytest tests/test_phase10_outage_safety.py tests/test_health.py -q`

### Console proof if touched
- `npm --prefix console run test -- --run src/components/health/runtime-health-cards.test.tsx`
- `npm --prefix console run test -- --run 'src/app/(console)/observability/page.test.tsx' 'src/app/(console)/observability/observability-page.test.tsx'`

### Optional browser/UAT only if blocker is cleared
- `npm --prefix console run test:e2e -- observability.spec.ts` or project-equivalent `make console-e2e`

## Constraints and Watch-outs
- Do **not** add a new resilience dashboard or recovery-specific API. Existing `/health/ready`, `/health/dependencies`, and Observability seams remain canonical.
- Keep hosted/control-plane language subordinate. `docs/hosted-reinforcement-boundary.md` explicitly says hosted freshness/posture is descriptive only and local runtime surfaces must confirm serving-time truth.
- Recovery proof must not overclaim. Showing `last_recovery_at` is supporting evidence, not proof of all downstream reconciliation unless request behavior and health status also agree.
- Prefer deterministic injected doubles over container/network fault choreography. S02 intentionally used deterministic harness-based outage proofs; S04 should preserve rerunnability.
- Because `RuntimeHealthCards` renders metadata generically, backend payload truth matters more than adding new console code. UI changes are probably unnecessary unless the planner chooses to add a tiny recovery-specific wording assertion.

## Sources
- `tests/test_phase10_outage_safety.py`
- `tests/test_health.py`
- `tests/support.py`
- `src/nebula/models/resilience.py`
- `src/nebula/services/runtime_health_service.py`
- `src/nebula/main.py`
- `console/src/lib/admin-api.ts`
- `console/src/components/health/runtime-health-cards.tsx`
- `console/src/app/(console)/observability/page.tsx`
- `console/e2e/observability.spec.ts`
- `docs/m009-integrated-proof.md`
- `docs/hosted-reinforcement-boundary.md`
