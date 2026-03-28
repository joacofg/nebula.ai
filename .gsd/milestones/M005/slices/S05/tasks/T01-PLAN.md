---
estimated_steps: 5
estimated_files: 7
skills_used: []
---

# T01: Author the pointer-only v4 integrated proof walkthrough

Create the new integrated v4 proof document that assembles the already-shipped S02-S04 seams into one strict review path. Follow the established integrated-proof doc pattern used elsewhere in `docs/`, keep canonical details delegated to existing sources, and make R044 scope discipline explicit so the walkthrough proves a narrow operator decisioning story instead of implying new platform scope.

Steps:
1. Use the existing integrated proof docs as style/structure references and draft a new `docs/v4-integrated-proof.md` that explains what the v4 proof establishes, the required proof order, the minimal operator walkthrough, what it intentionally does not duplicate, and the failure modes the proof makes obvious.
2. Ground the walkthrough in the shipped v4 seams only: route vocabulary, policy simulation replay, hard budget guardrails, bounded recommendations, semantic-cache tuning, Observability framing, and benchmark/evaluation artifacts; explicitly point back to the canonical docs and code-backed surfaces instead of restating contracts.
3. Keep the narrative pointer-only and scope-guarded: no new APIs, no new dashboard/page concept, no autonomous optimization language, no billing/analytics/SDK/hosted-authority expansion, and preserve the existing wording that recommendations are grounded, bounded, and operator-driven.

## Inputs

- ``docs/integrated-adoption-proof.md``
- ``docs/embeddings-integrated-adoption-proof.md``
- ``docs/hosted-integrated-adoption-proof.md``
- ``docs/route-decision-vocabulary.md``
- ``docs/policy-guardrails.md``
- ``docs/evaluation.md``
- ``console/src/app/(console)/observability/page.tsx``
- ``console/src/components/policy/policy-form.tsx``
- ``src/nebula/api/routes/admin.py``
- ``src/nebula/services/recommendation_service.py``
- ``src/nebula/models/governance.py``

## Expected Output

- ``docs/v4-integrated-proof.md``

## Verification

test -f docs/v4-integrated-proof.md && grep -c '^## ' docs/v4-integrated-proof.md | awk '{exit !($1 >= 6)}' && ! grep -q 'TODO\|TBD' docs/v4-integrated-proof.md

## Observability Impact

This task documents the canonical inspection path future agents should follow when v4 claims drift: simulation preview, recommendations/cache summary, usage-ledger evidence, and benchmark artifacts remain the runtime proof surfaces.
