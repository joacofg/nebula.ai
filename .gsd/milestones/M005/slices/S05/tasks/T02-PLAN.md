---
estimated_steps: 5
estimated_files: 10
skills_used: []
---

# T02: Wire discoverability and lock the integrated proof path with focused verification

Make the new v4 proof easy to find from existing documentation surfaces and prove the assembled v4 story still holds across backend, API, and console evidence paths. Keep documentation edits pointer-only, then add or update lightweight checks so close-out verification covers both behavior and discoverability.

Steps:
1. Add concise pointer-only references to `docs/v4-integrated-proof.md` from `README.md` and `docs/architecture.md`, placing the new walkthrough alongside existing integrated-proof entries without duplicating the v4 contract details there.
2. Add a narrow documentation integrity test or assertion file if needed so discoverability is mechanically checked without snapshotting long markdown prose; otherwise, make the verification commands explicitly check the file and both links.
3. Re-run the focused backend, admin API, and console tests that already prove simulation, guardrails, recommendations, cache controls, and operator wording, then include the doc existence/link checks in the verification story for this slice.

## Inputs

- ``docs/v4-integrated-proof.md``
- ``README.md``
- ``docs/architecture.md``
- ``tests/test_service_flows.py``
- ``tests/test_governance_api.py``
- ``console/src/app/(console)/observability/page.test.tsx``
- ``console/src/app/(console)/observability/observability-page.test.tsx``
- ``console/src/components/policy/policy-form.test.tsx``
- ``console/src/components/policy/policy-page.test.tsx``
- ``console/src/components/ledger/ledger-request-detail.test.tsx``

## Expected Output

- ``README.md``
- ``docs/architecture.md``
- ``docs/v4-integrated-proof.md``

## Verification

./.venv/bin/pytest tests/test_service_flows.py -k "simulation or recommendation or cache or runtime_policy or budget" -x && ./.venv/bin/pytest tests/test_governance_api.py -k "simulation or recommendation or guardrail or policy_options or policy_denied" -x && npm --prefix console run test -- --run src/app/'(console)'/observability/page.test.tsx src/app/'(console)'/observability/observability-page.test.tsx src/components/policy/policy-form.test.tsx src/components/policy/policy-page.test.tsx src/components/ledger/ledger-request-detail.test.tsx && test -f docs/v4-integrated-proof.md && rg -n "v4-integrated-proof\.md" README.md docs/architecture.md

## Observability Impact

Verification for this task explicitly preserves the known diagnostic surfaces: backend/API tests guard simulation and recommendation contracts, console tests guard operator wording, and doc link checks ensure reviewers can still find the assembled proof path.
