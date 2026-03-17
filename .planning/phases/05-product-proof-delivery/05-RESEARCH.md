# Phase 05: Product Proof & Delivery - Research

**Researched:** 2026-03-17
**Domain:** Benchmark proof, product documentation, and demo/pilot packaging for Nebula
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
## Implementation Decisions

### Benchmark proof story
- The benchmark suite should primarily prove Nebula's cost savings against an always-premium baseline, with degraded and fallback behavior included as supporting credibility proof rather than a separate equal-weight story.
- The benchmark comparison set should center on forced premium, forced local, auto-routing cold, auto-routing warm-cache, and forced fallback scenarios so the product story shows both savings and resilience from one canonical dataset.
- Phase 5 should ship one canonical repeatable benchmark suite plus a smaller demo-friendly subset that can be run live without too much setup or waiting.
- The benchmark proof should be legible to all three audiences, but the primary decision lens is startup engineering teams evaluating a pilot; academic-review clarity and live-demo readability should support that primary audience.

### Benchmark artifact shape
- Benchmark runs should continue producing machine-readable raw artifacts, but Phase 5 should add a stronger human-readable summary layer that surfaces key takeaways first instead of expecting readers to infer them from the table.
- The default artifact set should emphasize concise tables, benchmark summary callouts, route-distribution and cost-avoidance highlights, and explicit pass/fail notes for scenario expectation mismatches.
- Artifact output should stay repo-native and reviewable in Markdown/JSON rather than depending on a separate dashboard or notebook workflow for the core evaluation story.
- Charts may be added if they stay lightweight and portable, but Phase 5 should not depend on heavy visualization tooling to make the benchmark convincing.

### Demo narrative
- The preferred live-demo flow is benchmark-led but product-grounded: briefly show the operator console and playground, then demonstrate a benchmark run and its artifact summary, then show one intentional degraded/fallback scenario to prove the system stays explainable when local optimization fails.
- The live story should make one concrete claim: Nebula reduces estimated premium spend on repeatable traffic patterns without hiding routing or degraded behavior from the operator.
- Degraded behavior should be demonstrated deliberately, not treated as an aside, because it strengthens trust in the savings claim and connects back to Phase 3 and Phase 4 observability/governance work.
- The demo package should optimize for a smooth end-to-end walkthrough by one operator, not a long exploratory product tour.

### Documentation package
- Phase 5 documentation should be split into focused docs rather than forcing everything into the root README.
- The root README should become the fast product entrypoint: what Nebula is, why it exists, the key proof points, and where to go next for deploy/evaluate/demo details.
- The focused docs set should cover at least deployment, architecture, benchmarking/evaluation, and a live demo script so both pilot evaluators and academic reviewers can find the right level of detail quickly.
- Documentation should optimize first for an engineer evaluating or onboarding a pilot deployment, while still reading as a complete and defensible software engineering project for academic review.

### Claude's Discretion
- Exact doc filenames and internal section ordering, as long as the split between quick-start, architecture, evaluation, and demo material remains clear.
- Exact benchmark-summary wording and visual treatment, as long as the value story is explicit and defensible.
- Exact level of optional artifact polish beyond the required Markdown/JSON deliverables.

### Deferred Ideas (OUT OF SCOPE)
## Deferred Ideas

- Hosted trial/signup flows or customer-facing sales packaging — future commercialization work.
- Enterprise procurement/compliance documentation such as SSO, audit exports, or formal security packaging — future enterprise-readiness work.
- Standalone analytics dashboards or external BI-style reporting for benchmarks — separate future phase if needed.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| EVAL-01 | Operator can run a repeatable benchmark suite that compares local, premium, cache-hit, and fallback scenarios | Use the existing `BenchmarkRunner`, keep the versioned JSONL dataset, add a canonical suite plus demo subset, and make the artifact summary explicitly compare baseline premium spend against local/cache/fallback outcomes. |
| EVAL-02 | Benchmark artifacts summarize latency, route outcome, token usage, and estimated premium cost | Extend the current `report.md`/`report.json` rendering to include executive callouts, scenario-group summaries, pass/fail expectation notes, and cost-avoidance framing without replacing the current raw result rows. |
| DOCS-01 | Repository documentation includes a demo script, deployment guide, and architecture explanation suitable for academic review and pilot onboarding | Restructure the root `README.md` into an entrypoint and add focused docs for architecture, evaluation/benchmarking, and demo execution while keeping `docs/self-hosting.md` as the canonical deployment runbook. |
</phase_requirements>

## Summary

Phase 5 is packaging and proof work, not new product-surface work. The repo already has the core mechanics needed to satisfy the phase: a functioning benchmark runner in `src/nebula/benchmarking/run.py`, a scenario dataset in `benchmarks/v1/scenarios.jsonl`, an example artifact under `artifacts/benchmarks/20260314T193127Z/report.md`, a supported self-hosted deployment path in `docs/self-hosting.md` plus `docker-compose.selfhosted.yml`, and live demoable operator surfaces in the console playground and observability pages.

What is missing is the narrative layer. The current benchmark report is accurate but too raw for pilot evaluation or academic review, the docs are still concentrated in `README.md` plus one deployment guide, and there is no explicit repo-native demo package that ties the benchmark proof to the operator UI and degraded-behavior story. The planner should treat this phase as: strengthen the benchmark outputs first, then rewrite docs around those outputs, then lock the end-to-end pilot/demo workflow around the existing console and deployment surfaces.

The main planning risk is drift between the canonical story and the current implementation. The locked benchmark story centers on five comparison groups, but the dataset currently has six modes because `auto_complex` is still present. The phase should not remove working coverage casually; it should promote one canonical comparison frame for humans while deciding deliberately whether `auto_complex` remains a supporting premium-routed scenario or is folded into the premium control story.

**Primary recommendation:** Use the existing benchmark runner, dataset, self-hosted compose path, and console surfaces as the backbone; add a stronger Markdown/JSON evaluation layer and a focused documentation/demo package instead of inventing any new runtime, dashboard, or alternate deployment flow.

## What Exists Today

### Benchmark workflow
- `src/nebula/benchmarking/run.py` already runs versioned scenarios, spins managed local servers when `BASE_URL` is absent, writes `report.json` and `report.md`, computes route distribution, latency percentiles, cache/fallback rates, premium cost, and avoided premium cost.
- `src/nebula/benchmarking/dataset.py` already provides ordered scenario modes and grouping.
- `benchmarks/v1/scenarios.jsonl` already covers premium control, local control, auto-routing cold, auto-routing warm cache, premium-routed complex prompts, and fallback.
- `benchmarks/pricing.json` is already wired into both benchmarking and runtime cost estimation.
- `tests/test_benchmarking.py` already verifies dataset grouping, pricing math, report shape, and tenant-authenticated benchmark execution.

### Documentation and deployment
- `README.md` already explains local development, benchmarking, self-hosting, smoke tests, and endpoints, but it is overloaded and not optimized for pilot evaluators.
- `docs/self-hosting.md` already documents the single supported production-ish deployment path.
- `docker-compose.selfhosted.yml` and `deploy/selfhosted.env.example` already define the supported operator-facing topology and env contract.

### Demoable product surfaces
- `console/src/components/playground/playground-form.tsx`, `playground-metadata.tsx`, and `playground-recorded-outcome.tsx` already support the key “send request, inspect route/fallback/cost metadata, then compare with ledger outcome” flow.
- `console/src/components/health/runtime-health-cards.tsx` already expresses optional dependency degradation clearly enough to anchor the degraded-scenario trust story.
- `console/e2e/playground.spec.ts` and `console/e2e/observability.spec.ts` already cover the main operator flows that a demo package should reuse instead of replacing.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | `>=3.12` | Backend runtime and benchmark tooling | Already the project runtime; benchmark code and tests are implemented here. |
| FastAPI | `>=0.115.0,<1.0.0` | Gateway and admin API | Existing product contract and health/admin surfaces are already built on it. |
| httpx | `>=0.27.0,<1.0.0` | Benchmark client and test transport | Already used for benchmark execution and mocked request verification. |
| Next.js | `^15.2.2` | Operator console and demoable UI | Existing pilot/demo surface; no new frontend stack is justified. |
| React | `^19.0.0` | Console UI components | Existing operator workflows already rely on it. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | `>=8.2.0,<9.0.0` | Backend/unit verification | Use for benchmark report rendering, dataset shaping, and doc-adjacent backend assertions. |
| pytest-asyncio | `>=0.23.0,<1.0.0` | Async backend tests | Use when benchmark runner behavior depends on async HTTP flows. |
| Vitest | `3.2.4` via lockfile | Console component verification | Use if Phase 5 adds any UI copy or structural changes for demo surfaces. |
| Playwright | `1.58.2` via lockfile | Browser workflow verification | Use for pilot/demo flow regressions across playground and observability pages. |
| Docker Compose | repo-managed | Supported self-hosted topology | Use for deployment docs and live demo prep; do not introduce another supported runtime path. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Repo-native Markdown/JSON artifacts | Notebook/dashboard workflow | Better visuals, but violates the locked requirement to keep evaluation reviewable in-repo and adds delivery friction. |
| Existing console screens for demos | Separate demo microsite or slideware-only flow | Looks polished faster, but disconnects the proof from the actual product and creates maintenance drift. |
| Current compose deployment path | Kubernetes/Terraform packaging | Broader deployment story, but out of scope and weakens the single-path onboarding story. |

**Installation:**
```bash
make install
npm --prefix console install
```

## Architecture Patterns

### Recommended Project Structure
```text
benchmarks/
├── pricing.json                  # Cost assumptions used by runtime and evaluation
└── v1/scenarios.jsonl            # Canonical repeatable benchmark suite
artifacts/
└── benchmarks/<timestamp>/       # Generated report.json/report.md outputs
docs/
├── self-hosting.md               # Canonical deployment runbook
├── architecture.md               # Phase 5 addition
├── evaluation.md                 # Phase 5 addition
└── demo-script.md                # Phase 5 addition
README.md                         # Product entrypoint and doc index
```

### Pattern 1: Benchmark As Black-Box Product Proof
**What:** Keep benchmark execution API-driven and header-observed instead of adding direct service hooks or test-only introspection.
**When to use:** For canonical benchmark and demo-friendly subset runs that need to read like operator-evaluable product proof.
**Example:**
```python
payload = {
    "model": self._requested_model_for_mode(scenario.mode),
    "messages": self._effective_messages(scenario),
}
headers = {
    "X-Nebula-API-Key": self.settings.bootstrap_api_key,
    "X-Nebula-Tenant-ID": self.settings.bootstrap_tenant_id,
}
response = await client.post("/v1/chat/completions", json=payload, headers=headers)
route_target = response.headers.get("X-Nebula-Route-Target")
fallback_used = response.headers.get("X-Nebula-Fallback-Used") == "true"
```
Source: local implementation in `src/nebula/benchmarking/run.py`

### Pattern 2: Human Summary Layer Over Raw Artifacts
**What:** Preserve the raw scenario table and JSON data, but place executive takeaways first in Markdown.
**When to use:** For `report.md` and any doc pages that summarize benchmark output.
**Example:**
```python
return {
    "summary": {
        "route_distribution": route_distribution,
        "cache_hit_rate": ...,
        "fallback_rate": ...,
        "estimated_premium_cost": ...,
        "estimated_premium_cost_avoided": ...,
        "scenario_failures": {...},
    },
    "results": report_results,
}
```
Source: local implementation in `src/nebula/benchmarking/run.py`

### Pattern 3: Docs Split By Reader Task
**What:** Keep `README.md` as the entrypoint and move deep detail into focused docs.
**When to use:** For Phase 5 documentation work. Deployment stays in `docs/self-hosting.md`; architecture, evaluation, and demo guides should become peer documents.
**Example:** `README.md` should answer “what is Nebula, why it matters, how to prove it, where to deploy, where to demo” and then link out.

### Pattern 4: Demo Around Existing Operator Surfaces
**What:** Use the playground for live routing proof and observability/runtime health for degraded-state proof.
**When to use:** For demo docs, screenshots, browser checks, and pilot walkthroughs.
**Example:** `console/e2e/playground.spec.ts` already validates request metadata plus recorded ledger outcome; `console/e2e/observability.spec.ts` already validates degraded dependency messaging.

### Anti-Patterns to Avoid
- **Second supported deployment path:** Do not document local-dev startup as a production-ish onboarding path. `docs/self-hosting.md` plus Compose is the canonical route.
- **Benchmark as raw log dump:** The current `report.md` is useful but not persuasive enough. Phase 5 should not stop at row-level tables.
- **Separate demo-only UI:** Reuse the existing console; otherwise the proof package diverges from the product.
- **Hidden degraded behavior:** The locked story requires intentional degraded/fallback demonstration, not a best-case-only walkthrough.

## Gaps To Close

| Area | Current State | Gap |
|------|---------------|-----|
| Benchmark narrative | `report.md` exposes totals and a full scenario table | Missing executive callouts, canonical comparison framing, and explicit “why this proves value” language |
| Canonical scenario story | Dataset includes six modes including `auto_complex` | Locked story is centered on five comparison groups; Phase 5 needs a deliberate human-facing grouping model |
| Demo-friendly subset | Only one full dataset exists today | Missing a smaller, fast live-demo subset and instructions for when to use each suite |
| Documentation split | `README.md` + `docs/self-hosting.md` only | Missing dedicated architecture, evaluation, and demo docs |
| Pilot package | Console flows exist, but no packaged walkthrough | Missing a single operator-run sequence connecting setup, benchmark artifacts, playground, and degraded-state proof |
| Docs verification | Test infra exists, docs coverage does not | Missing simple existence/consistency checks and a manual acceptance checklist for content quality |

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Benchmark visualization | Separate dashboard, BI export, or notebook pipeline | Existing `report.json` + improved `report.md` | Keeps artifacts portable, reviewable, and aligned with locked decisions. |
| Demo surface | Standalone demo UI or throwaway scripts that bypass product flows | Existing console playground and observability views | Avoids drift and proves the shipped product, not a staging artifact. |
| Deployment packaging | Additional supported deploy targets | `docker-compose.selfhosted.yml` and `docs/self-hosting.md` | Preserves one credible onboarding path. |
| Cost logic | Duplicate pricing calculators for docs or scripts | `benchmarks/pricing.json` + `PricingCatalog` | Prevents inconsistent spend claims between runtime and benchmark artifacts. |

**Key insight:** Phase 5 should package and explain the product Nebula already has. Any custom delivery surface that bypasses the benchmark runner, pricing catalog, or supported compose topology will create trust and maintenance problems immediately.

## Common Pitfalls

### Pitfall 1: Treating `BASE_URL` mode as equivalent to full proof mode
**What goes wrong:** External-server benchmark runs skip fallback scenarios by design.
**Why it happens:** `BenchmarkRunner.run()` only executes fallback scenarios when it controls the managed local server configuration.
**How to avoid:** Make the canonical proof command use managed-local execution and document `BASE_URL` mode as a reduced-scope convenience path.
**Warning signs:** Artifact summary shows skipped fallback scenarios or incomplete comparison groups.

### Pitfall 2: Letting the raw scenario table carry the whole product story
**What goes wrong:** Readers have to infer value from dozens of cells and tiny cost numbers.
**Why it happens:** The current report renderer writes totals and a single table, but no “headline” interpretation.
**How to avoid:** Add top-level summary callouts that answer savings, route mix, cache effect, fallback credibility, and scenario mismatches explicitly.
**Warning signs:** A reviewer can read `report.md` and still not answer “how much premium spend did Nebula avoid?” quickly.

### Pitfall 3: Allowing documentation drift between README and focused docs
**What goes wrong:** Setup, architecture, and evaluation instructions contradict each other.
**Why it happens:** `README.md` already contains deployment and benchmark instructions that will need to be split out.
**How to avoid:** Keep README concise and link-oriented; treat `docs/self-hosting.md` as the source of truth for deployment and make the new focused docs own their domains.
**Warning signs:** Multiple files define the supported topology or benchmark commands differently.

### Pitfall 4: Hiding degraded behavior from the benchmark-led demo
**What goes wrong:** The demo shows savings but not resilience or explainability, which weakens trust.
**Why it happens:** Best-case demos are easier to run than intentional fallback/degraded scenarios.
**How to avoid:** Include one deliberate degraded/fallback step using the existing health cards and fallback metadata surfaces.
**Warning signs:** Demo steps never visit observability or runtime health, and fallback remains only a report row.

### Pitfall 5: Accidentally changing the benchmark story while chasing polish
**What goes wrong:** Scenario set, naming, or cost assumptions change in ways that make comparisons non-repeatable.
**Why it happens:** Phase 5 is packaging-heavy, so it is easy to over-edit the underlying dataset.
**How to avoid:** Keep `benchmarks/v1/scenarios.jsonl` versioned and stable, introduce any demo subset as an explicit additional artifact or dataset, and document pricing assumptions clearly.
**Warning signs:** Scenario counts drift without updated tests, or spend claims no longer trace back to `benchmarks/pricing.json`.

## Code Examples

Verified patterns from the current repo:

### Report Artifact Generation
```python
report = self._build_report(results)
artifact_dir = self.artifacts_root / self.run_id
artifact_dir.mkdir(parents=True, exist_ok=True)
(artifact_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
(artifact_dir / "report.md").write_text(self._render_markdown(report), encoding="utf-8")
```
Source: `src/nebula/benchmarking/run.py`

### Current Summary Metrics
```python
"summary": {
    "total_requests": total_requests,
    "passed": ...,
    "failed": ...,
    "route_distribution": route_distribution,
    "cache_hit_rate": ...,
    "fallback_rate": ...,
    "latency_by_mode_ms": {...},
    "estimated_premium_cost": ...,
    "estimated_premium_cost_avoided": ...,
    "scenario_failures": {...},
}
```
Source: `src/nebula/benchmarking/run.py`

### Existing Degraded-State Operator Messaging
```tsx
{hasOptionalDegradation ? (
  <div className="rounded-xl border border-amber-200 bg-amber-50 px-6 py-4 text-sm text-amber-900">
    Optional dependency degradation does not block gateway readiness.
  </div>
) : null}
```
Source: `console/src/components/health/runtime-health-cards.tsx`

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Prototype-style README with mixed setup and product notes | Operator-first self-hosted + benchmark story, but still concentrated in README | Phases 1-4 | Phase 5 should complete the transition into a real product/documentation package. |
| Raw benchmark execution as developer tooling | Benchmarking already emits versioned repo artifacts with cost and route metrics | Before Phase 5 | The remaining work is narrative clarity, not core benchmark infrastructure. |
| API-only operator proof | Console playground and observability workflows exist with browser coverage | Phases 2-4 | Demo packaging should lean on these surfaces directly. |

**Deprecated/outdated:**
- Treating local development steps in `README.md` as equivalent to deployment guidance: `docs/self-hosting.md` is already the canonical supported deployment path.
- Treating benchmark totals alone as sufficient evidence: the current artifact is technically correct but not decision-ready for pilot evaluation.

## Recommended Plan Seams

### 05-01: Strengthen benchmark workflows and reports
- Keep the runner/dataset architecture intact and focus on artifact shape.
- Add a canonical human-readable summary section to `report.md` and matching structured fields in `report.json`.
- Introduce a demo-friendly subset path without replacing the full canonical suite.
- Decide explicitly how `auto_complex` participates in the human-facing comparison story.
- Extend backend tests around report summary rendering, scenario grouping, and skipped-fallback messaging.

### 05-02: Produce deployment, architecture, and demo documentation
- Rewrite `README.md` into a product entrypoint with proof points and links.
- Preserve `docs/self-hosting.md` as the deployment source of truth.
- Add focused docs for architecture, evaluation/benchmarking, and the live demo script.
- Keep all instructions anchored to existing compose/env/console surfaces.
- Add lightweight verification for doc existence and command consistency where practical.

### 05-03: Polish the end-to-end pilot/demo package
- Package the live walkthrough around one operator journey: deploy, prove with benchmark artifact, show playground metadata, show recorded ledger outcome, then show degraded/fallback observability.
- Reuse current playground and observability UI, and add any minimal polish/copy required for demo clarity.
- Add or update Playwright coverage only where the demo path is not already locked down.
- Produce one concise checklist for pilot/demo readiness and artifact capture.

## Open Questions

1. **Should `auto_complex` remain a separate scenario mode in the canonical human-facing story?**
   - What we know: It exists today and provides premium-routed coverage.
   - What's unclear: Whether the planner should present it as its own comparison bucket or fold it into the premium baseline narrative.
   - Recommendation: Keep the dataset coverage, but decide in 05-01 whether the summary groups it under premium-routed scenarios while the five locked comparison groups remain the top-line story.

2. **How small should the live demo subset be?**
   - What we know: The context requires a faster subset and warns against a long live run.
   - What's unclear: Exact target runtime and which scenarios must be included for a convincing live proof.
   - Recommendation: Plan for one scenario each from premium control, local/cache proof, and fallback proof unless measurement shows a slightly larger subset is still fast enough.

3. **Do Phase 5 docs need screenshot assets committed to the repo?**
   - What we know: Existing product surfaces are demoable and Playwright-covered.
   - What's unclear: Whether static screenshots materially improve academic/pilot packaging or create maintenance burden.
   - Recommendation: Treat screenshots as optional polish in 05-03, not a blocking requirement for 05-02.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Mixed: `pytest` 8.x, `Vitest` 3.2.4, `Playwright` 1.58.2 |
| Config file | `pyproject.toml`, `console/vitest.config.ts`, `console/playwright.config.ts` |
| Quick run command | `./.venv/bin/pytest tests/test_benchmarking.py -x && npm --prefix console run e2e -- playground.spec.ts observability.spec.ts` |
| Full suite command | `make test && npm --prefix console run test -- --run && npm --prefix console run e2e` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EVAL-01 | Repeatable benchmark suite covers premium, local, cache-hit, and fallback scenarios | unit/integration | `./.venv/bin/pytest tests/test_benchmarking.py -x` | ✅ |
| EVAL-02 | Artifact summary exposes latency, route outcome, token usage, estimated premium cost, and expectation mismatches | unit | `./.venv/bin/pytest tests/test_benchmarking.py -x` | ✅ |
| DOCS-01 | Repo includes deployment guide, architecture explanation, evaluation guide, and demo script aligned to actual product flows | manual-plus-shell | `test -f README.md && test -f docs/self-hosting.md && test -f docs/architecture.md && test -f docs/evaluation.md && test -f docs/demo-script.md` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `./.venv/bin/pytest tests/test_benchmarking.py -x` for benchmark/report changes, `npm --prefix console run test -- --run` for console-only copy/structure changes
- **Per wave merge:** `./.venv/bin/pytest tests/test_benchmarking.py -x && npm --prefix console run e2e -- playground.spec.ts observability.spec.ts`
- **Phase gate:** `make test && npm --prefix console run test -- --run && npm --prefix console run e2e`

### Wave 0 Gaps
- [ ] `docs/architecture.md` — required for DOCS-01
- [ ] `docs/evaluation.md` — required for DOCS-01
- [ ] `docs/demo-script.md` — required for DOCS-01
- [ ] Extend `tests/test_benchmarking.py` to lock new summary fields, canonical group framing, and demo-subset behavior
- [ ] Add a lightweight docs existence/consistency check script or equivalent CI-friendly command for DOCS-01

## Sources

### Primary (HIGH confidence)
- Local context: `.planning/phases/05-product-proof-delivery/05-CONTEXT.md`
- Local requirements: `.planning/REQUIREMENTS.md`
- Local roadmap and project framing: `.planning/ROADMAP.md`, `.planning/PROJECT.md`, `.planning/STATE.md`
- Benchmark implementation: `src/nebula/benchmarking/run.py`, `src/nebula/benchmarking/dataset.py`, `benchmarks/v1/scenarios.jsonl`, `benchmarks/pricing.json`
- Existing benchmark artifact: `artifacts/benchmarks/20260314T193127Z/report.md`
- Deployment and docs surfaces: `README.md`, `docs/self-hosting.md`, `docker-compose.selfhosted.yml`, `deploy/selfhosted.env.example`
- Demo/product surfaces: `console/src/components/playground/playground-form.tsx`, `console/src/components/playground/playground-metadata.tsx`, `console/src/components/playground/playground-recorded-outcome.tsx`, `console/src/components/health/runtime-health-cards.tsx`
- Validation surfaces: `tests/test_benchmarking.py`, `console/e2e/playground.spec.ts`, `console/e2e/observability.spec.ts`, `pyproject.toml`, `console/package.json`, `console/vitest.config.ts`, `console/playwright.config.ts`, `Makefile`

### Secondary (MEDIUM confidence)
- None needed; this research is grounded in current repo state and local planning artifacts.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Derived from repo-pinned dependencies and currently shipped product surfaces.
- Architecture: HIGH - Based on implemented benchmark, deployment, console, and planning artifacts.
- Pitfalls: HIGH - Directly traceable to current runner behavior, docs layout, and locked Phase 5 decisions.

**Research date:** 2026-03-17
**Valid until:** 2026-04-16

## Final Recommendation

Split Phase 5 exactly along the roadmap seams:

1. `05-01` should be backend-artifact work: make the benchmark outputs persuasive, keep them repeatable, and add the demo-sized subset.
2. `05-02` should be documentation architecture work: convert `README.md` into an entrypoint and add focused deployment, architecture, evaluation, and demo docs.
3. `05-03` should be delivery polish: package one operator-led pilot/demo flow that reuses the existing console and validates the end-to-end proof story.
