# Phase 5: Product Proof & Delivery - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Finish Nebula's benchmark proof, product-facing documentation, and pilot/demo packaging so the project reads as a credible self-hosted B2B gateway with measurable value. This phase sharpens how Nebula proves cost savings and reliability, how those results are explained in docs and demo materials, and how another engineer can deploy, understand, and evaluate the system. It does not add new gateway capabilities, new console features, hosted-product scope, or broader enterprise packaging.

</domain>

<decisions>
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

</decisions>

<specifics>
## Specific Ideas

- The strongest Phase 5 story is not "Nebula has many features"; it is "Nebula can prove when it saves money, when it falls back, and why."
- The benchmark output should read more like an evaluation package than a raw developer log.
- The demo should intentionally include one degraded or fallback moment instead of trying to hide operational rough edges.
- The docs should help two adjacent readers quickly: an engineer deciding whether to trial Nebula, and an academic evaluator assessing completeness and rigor.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and phase framing
- `.planning/PROJECT.md` — Product thesis, target users, self-hosted constraints, and the academic-evaluation requirement that shapes Phase 5 packaging.
- `.planning/REQUIREMENTS.md` — Phase 5 requirements `EVAL-01`, `EVAL-02`, and `DOCS-01`.
- `.planning/ROADMAP.md` — Phase 5 goal, success criteria, and plan breakdown for benchmark proof, docs, and demo packaging.
- `.planning/STATE.md` — Current project position and carry-forward decisions from completed phases.

### Prior phase decisions that constrain Phase 5
- `.planning/phases/01-self-hosted-foundation/01-CONTEXT.md` — Canonical self-hosted deployment story, premium-first runtime, and degraded-dependency positioning.
- `.planning/phases/02-operator-console/02-CONTEXT.md` — Operator-console tone and admin-managed trust model that the demo/docs should preserve.
- `.planning/phases/04-governance-hardening/04-CONTEXT.md` — Runtime-authoritative policy boundary and explainability expectations that the product proof should reflect.

### Benchmark and evaluation sources
- `src/nebula/benchmarking/run.py` — Current benchmark orchestration, artifact generation, and report shape.
- `src/nebula/benchmarking/dataset.py` — Scenario model and grouping behavior for the benchmark suite.
- `benchmarks/v1/scenarios.jsonl` — Canonical scenario set currently covering premium, local, cache, and fallback paths.
- `benchmarks/pricing.json` — Estimated pricing catalog used for premium-cost calculations.
- `tests/test_benchmarking.py` — Existing behavioral expectations for report generation and tenant-authenticated benchmark execution.
- `artifacts/benchmarks/20260314T193127Z/report.md` — Concrete example of the current benchmark artifact shape and proof baseline.

### Operator and deployment docs surface
- `README.md` — Current root documentation and benchmark/self-hosted entrypoint that Phase 5 should strengthen.
- `docs/self-hosting.md` — Current deploy runbook and supported topology that broader documentation must stay consistent with.
- `docker-compose.selfhosted.yml` — Supported self-hosted stack the deployment and demo docs should reference.
- `deploy/selfhosted.env.example` — Canonical environment template for deployment guidance.

### Demoable product surfaces
- `console/src/components/playground/playground-form.tsx` — Existing live request entrypoint suitable for demo setup.
- `console/src/components/playground/playground-metadata.tsx` — Operator-visible routing/cache/fallback metadata surfaced during demos.
- `console/src/components/playground/playground-recorded-outcome.tsx` — Persisted outcome details that connect immediate responses to ledger data.
- `console/src/components/health/runtime-health-cards.tsx` — Dependency/degraded-state UI already available for demo and docs.
- `console/e2e/playground.spec.ts` — Existing browser-level expectations around the playground flow.
- `console/e2e/observability.spec.ts` — Existing operator-observability flow that can inform the pilot/demo package.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/nebula/benchmarking/run.py`: already produces timestamped JSON and Markdown artifacts, computes estimated premium cost and avoided cost, and supports managed-local versus external-server execution modes.
- `benchmarks/v1/scenarios.jsonl`: already covers the core proof categories Phase 5 cares about: premium control, local control, cold auto-routing, warm-cache auto-routing, and fallback.
- `artifacts/benchmarks/*/report.md`: gives a concrete baseline artifact to improve instead of inventing a brand-new evaluation format.
- `README.md` and `docs/self-hosting.md`: already provide the minimum deployment and benchmark story, so Phase 5 should restructure and deepen docs rather than start from zero.
- `console/src/components/playground/*` and `console/src/components/health/runtime-health-cards.tsx`: already expose live product surfaces that can anchor a demo script and operator-facing screenshots or walkthroughs.

### Established Patterns
- Benchmarking currently proves behavior through the public API and response headers rather than direct internal hooks; Phase 5 should preserve that black-box evaluation style.
- Generated benchmark artifacts live under `artifacts/benchmarks/<timestamp>/`, so any report improvements should fit that existing artifact lifecycle.
- Documentation has stayed lightweight and repo-local so far; Phase 5 should preserve that portability and keep the core proof package readable directly from the repository.
- Earlier phases consistently favored explicit operator visibility over hidden automation, which argues for docs and demo materials that show route decisions, fallback, and degraded states plainly.

### Integration Points
- Benchmark-proof improvements connect the scenario dataset, benchmark runner, artifact renderer, and test suite.
- Documentation improvements connect `README.md`, `docs/`, deployment assets, and the current Compose/env setup.
- Demo packaging connects the console playground, runtime-health views, and benchmark artifacts into one repeatable walkthrough.
- Any benchmark-summary enhancements should be validated against the current test strategy in `tests/test_benchmarking.py` and any new artifact expectations added there.

</code_context>

<deferred>
## Deferred Ideas

- Hosted trial/signup flows or customer-facing sales packaging — future commercialization work.
- Enterprise procurement/compliance documentation such as SSO, audit exports, or formal security packaging — future enterprise-readiness work.
- Standalone analytics dashboards or external BI-style reporting for benchmarks — separate future phase if needed.

</deferred>

---

*Phase: 05-product-proof-delivery*
*Context gathered: 2026-03-17*
