# S05: Integrated v4 proof

**Goal:** Assemble the shipped v4 decisioning surfaces into one pointer-only integrated proof path that demonstrates simulation, hard guardrails, recommendations, cache controls, and benchmark evidence work together end to end without widening Nebula beyond interpretable, operator-driven decisioning scope.
**Demo:** After this: The full v4 decisioning story is assembled end to end and stays narrow, interpretable, and convincingly better than the prior heuristic posture.

## Tasks
- [x] **T01: Added a pointer-only v4 integrated proof walkthrough that ties together the shipped decisioning seams without expanding Nebula beyond operator-driven scope.** — Create the new integrated v4 proof document that assembles the already-shipped S02-S04 seams into one strict review path. Follow the established integrated-proof doc pattern used elsewhere in `docs/`, keep canonical details delegated to existing sources, and make R044 scope discipline explicit so the walkthrough proves a narrow operator decisioning story instead of implying new platform scope.

Steps:
1. Use the existing integrated proof docs as style/structure references and draft a new `docs/v4-integrated-proof.md` that explains what the v4 proof establishes, the required proof order, the minimal operator walkthrough, what it intentionally does not duplicate, and the failure modes the proof makes obvious.
2. Ground the walkthrough in the shipped v4 seams only: route vocabulary, policy simulation replay, hard budget guardrails, bounded recommendations, semantic-cache tuning, Observability framing, and benchmark/evaluation artifacts; explicitly point back to the canonical docs and code-backed surfaces instead of restating contracts.
3. Keep the narrative pointer-only and scope-guarded: no new APIs, no new dashboard/page concept, no autonomous optimization language, no billing/analytics/SDK/hosted-authority expansion, and preserve the existing wording that recommendations are grounded, bounded, and operator-driven.
  - Estimate: 45m
  - Files: docs/v4-integrated-proof.md, docs/route-decision-vocabulary.md, docs/policy-guardrails.md, docs/evaluation.md, docs/integrated-adoption-proof.md, docs/embeddings-integrated-adoption-proof.md, docs/hosted-integrated-adoption-proof.md
  - Verify: test -f docs/v4-integrated-proof.md && grep -c '^## ' docs/v4-integrated-proof.md | awk '{exit !($1 >= 6)}' && ! grep -q 'TODO\|TBD' docs/v4-integrated-proof.md
- [x] **T02: Added pointer-only README and architecture links for the v4 integrated proof and verified the end-to-end decisioning story across backend, admin API, console, and docs.** — Make the new v4 proof easy to find from existing documentation surfaces and prove the assembled v4 story still holds across backend, API, and console evidence paths. Keep documentation edits pointer-only, then add or update lightweight checks so close-out verification covers both behavior and discoverability.

Steps:
1. Add concise pointer-only references to `docs/v4-integrated-proof.md` from `README.md` and `docs/architecture.md`, placing the new walkthrough alongside existing integrated-proof entries without duplicating the v4 contract details there.
2. Add a narrow documentation integrity test or assertion file if needed so discoverability is mechanically checked without snapshotting long markdown prose; otherwise, make the verification commands explicitly check the file and both links.
3. Re-run the focused backend, admin API, and console tests that already prove simulation, guardrails, recommendations, cache controls, and operator wording, then include the doc existence/link checks in the verification story for this slice.
  - Estimate: 45m
  - Files: README.md, docs/architecture.md, docs/v4-integrated-proof.md, tests/test_governance_api.py, tests/test_service_flows.py, console/src/app/(console)/observability/page.test.tsx, console/src/app/(console)/observability/observability-page.test.tsx, console/src/components/policy/policy-form.test.tsx, console/src/components/policy/policy-page.test.tsx, console/src/components/ledger/ledger-request-detail.test.tsx
  - Verify: ./.venv/bin/pytest tests/test_service_flows.py -k "simulation or recommendation or cache or runtime_policy or budget" -x && ./.venv/bin/pytest tests/test_governance_api.py -k "simulation or recommendation or guardrail or policy_options or policy_denied" -x && npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx && test -f docs/v4-integrated-proof.md && rg -n "v4-integrated-proof\.md" README.md docs/architecture.md
