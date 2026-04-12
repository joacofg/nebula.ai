---
estimated_steps: 1
estimated_files: 8
skills_used: []
---

# T02: Expose retention lifecycle health and prove end-to-end deletion through real seams

Extend runtime health to include a `retention_lifecycle` dependency payload with truthful readiness/degraded state, last-run timestamps/results, and last error details while keeping the hosted plane metadata-only and bounded to dependency summaries rather than raw cleanup payloads. Use the lifecycle service added in T01 as the single source for this health data. Add backend tests that seed expired and surviving governed rows through the normal ledger path, invoke lifecycle cleanup through the running app/container seam, and verify `/v1/admin/usage/ledger` no longer returns expired rows while surviving/no-expiration rows remain. Re-verify hosted heartbeat/dependency summary behavior so the extra dependency name does not widen the export contract, and add/update console runtime-health tests only as needed to confirm the new dependency renders truthfully in existing observability cards without creating a retention dashboard. Keep request-detail/operator proof on existing seams. Record expected executor skills in frontmatter as `fastapi-python`, `react-best-practices`, and `userinterface-wiki`. Include Failure Modes, Load Profile, and Negative Tests in the task plan because this task spans app health, hosted summarization, operator surfaces, and retention edge cases.

## Inputs

- ``src/nebula/services/retention_lifecycle_service.py``
- ``src/nebula/services/runtime_health_service.py``
- ``src/nebula/services/heartbeat_service.py``
- ``src/nebula/api/routes/admin.py``
- ``tests/test_governance_api.py``
- ``tests/test_health.py``
- ``tests/test_hosted_contract.py``
- ``console/src/components/health/runtime-health-cards.tsx``
- ``console/src/components/health/runtime-health-cards.test.tsx``
- ``console/src/app/(console)/observability/page.tsx``
- ``console/src/app/(console)/observability/page.test.tsx``

## Expected Output

- ``src/nebula/services/runtime_health_service.py``
- ``src/nebula/services/heartbeat_service.py``
- ``tests/test_governance_api.py``
- ``tests/test_health.py``
- ``tests/test_hosted_contract.py``
- ``console/src/components/health/runtime-health-cards.tsx``
- ``console/src/components/health/runtime-health-cards.test.tsx``
- ``console/src/app/(console)/observability/page.test.tsx``

## Verification

./.venv/bin/pytest tests/test_governance_api.py tests/test_health.py tests/test_hosted_contract.py -k "retention or health or heartbeat" && npm --prefix console run test -- --run src/components/health/runtime-health-cards.test.tsx src/app/(console)/observability/page.test.tsx

## Observability Impact

Makes cleanup execution, last result, and failure state inspectable through runtime health and existing observability cards; validates that hosted only sees summarized dependency state.
