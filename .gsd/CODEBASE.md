# Codebase Map

Generated: 2026-04-27T15:00:11Z | Files: 242 | Described: 0/242
<!-- gsd:codebase-meta {"generatedAt":"2026-04-27T15:00:11Z","fingerprint":"38dda27523c597e2f46037a3ad619ce720ede8b7","fileCount":242,"truncated":false} -->

### (root)/
- `.dockerignore`
- `.env.example`
- `.gitignore`
- `.python-version`
- `.tmp_s05_research.md`
- `alembic.ini`
- `docker-compose.selfhosted.yml`
- `docker-compose.yml`
- `Dockerfile`
- `Makefile`
- `pyproject.toml`
- `README.md`

### .tmp/
- `.tmp/M006-S02-RESEARCH.md`
- `.tmp/s04_research.md`

### benchmarks/
- `benchmarks/pricing.json`

### benchmarks/v1/
- `benchmarks/v1/demo-scenarios.jsonl`
- `benchmarks/v1/scenarios.jsonl`

### console/
- `console/.env.example`
- `console/.eslintrc.json`
- `console/Dockerfile`
- `console/next-env.d.ts`
- `console/next.config.ts`
- `console/package-lock.json`
- `console/package.json`
- `console/playwright.config.ts`
- `console/postcss.config.mjs`
- `console/tailwind.config.ts`
- `console/tsconfig.json`
- `console/vitest.config.ts`

### console/e2e/
- `console/e2e/api-keys.spec.ts`
- `console/e2e/auth.spec.ts`
- `console/e2e/deployments-proof.spec.ts`
- `console/e2e/observability.spec.ts`
- `console/e2e/playground.spec.ts`
- `console/e2e/policy.spec.ts`
- `console/e2e/tenants.spec.ts`
- `console/e2e/trust-boundary.spec.ts`

### console/src/app/
- `console/src/app/globals.css`
- `console/src/app/layout.tsx`
- `console/src/app/page.tsx`
- `console/src/app/providers.tsx`

### console/src/app/(console)/
- `console/src/app/(console)/layout.tsx`

### console/src/app/(console)/api-keys/
- `console/src/app/(console)/api-keys/page.tsx`

### console/src/app/(console)/deployments/
- `console/src/app/(console)/deployments/page.test.tsx`
- `console/src/app/(console)/deployments/page.tsx`

### console/src/app/(console)/observability/
- `console/src/app/(console)/observability/observability-page.test.tsx`
- `console/src/app/(console)/observability/page.test.tsx`
- `console/src/app/(console)/observability/page.tsx`

### console/src/app/(console)/playground/
- `console/src/app/(console)/playground/page.tsx`

### console/src/app/(console)/policy/
- `console/src/app/(console)/policy/page.tsx`

### console/src/app/(console)/tenants/
- `console/src/app/(console)/tenants/page.test.tsx`
- `console/src/app/(console)/tenants/page.tsx`

### console/src/app/api/admin/[...path]/
- `console/src/app/api/admin/[...path]/route.ts`

### console/src/app/api/playground/completions/
- `console/src/app/api/playground/completions/route.ts`

### console/src/app/api/runtime/health/
- `console/src/app/api/runtime/health/route.ts`

### console/src/app/trust-boundary/
- `console/src/app/trust-boundary/page.test.tsx`
- `console/src/app/trust-boundary/page.tsx`

### console/src/components/api-keys/
- `console/src/components/api-keys/api-key-table.test.tsx`
- `console/src/components/api-keys/api-key-table.tsx`
- `console/src/components/api-keys/create-api-key-dialog.test.tsx`
- `console/src/components/api-keys/create-api-key-dialog.tsx`
- `console/src/components/api-keys/reveal-api-key-dialog.test.tsx`
- `console/src/components/api-keys/reveal-api-key-dialog.tsx`

### console/src/components/auth/
- `console/src/components/auth/admin-login-form.test.tsx`
- `console/src/components/auth/admin-login-form.tsx`
- `console/src/components/auth/login-page-client.tsx`

### console/src/components/deployments/
- `console/src/components/deployments/create-deployment-slot-drawer.tsx`
- `console/src/components/deployments/dependency-health-pills.tsx`
- `console/src/components/deployments/deployment-detail-drawer.tsx`
- `console/src/components/deployments/deployment-status-badge.tsx`
- `console/src/components/deployments/deployment-table.test.tsx`
- `console/src/components/deployments/deployment-table.tsx`
- `console/src/components/deployments/enrollment-token-reveal-dialog.tsx`
- `console/src/components/deployments/fleet-posture-summary.test.tsx`
- `console/src/components/deployments/fleet-posture-summary.tsx`
- `console/src/components/deployments/fleet-posture.test.ts`
- `console/src/components/deployments/fleet-posture.ts`
- `console/src/components/deployments/freshness-badge.test.tsx`
- `console/src/components/deployments/freshness-badge.tsx`
- `console/src/components/deployments/remote-action-card.test.tsx`
- `console/src/components/deployments/remote-action-card.tsx`
- `console/src/components/deployments/revoke-confirmation-dialog.tsx`
- `console/src/components/deployments/unlink-confirmation-dialog.tsx`

### console/src/components/health/
- `console/src/components/health/runtime-health-cards.test.tsx`
- `console/src/components/health/runtime-health-cards.tsx`

### console/src/components/hosted/
- `console/src/components/hosted/trust-boundary-card.test.tsx`
- `console/src/components/hosted/trust-boundary-card.tsx`

### console/src/components/ledger/
- `console/src/components/ledger/ledger-filters.test.tsx`
- `console/src/components/ledger/ledger-filters.tsx`
- `console/src/components/ledger/ledger-request-detail.test.tsx`
- `console/src/components/ledger/ledger-request-detail.tsx`
- `console/src/components/ledger/ledger-table.test.tsx`
- `console/src/components/ledger/ledger-table.tsx`

### console/src/components/playground/
- `console/src/components/playground/playground-form.test.tsx`
- `console/src/components/playground/playground-form.tsx`
- `console/src/components/playground/playground-metadata.test.tsx`
- `console/src/components/playground/playground-metadata.tsx`
- `console/src/components/playground/playground-page.test.tsx`
- `console/src/components/playground/playground-recorded-outcome.test.tsx`
- `console/src/components/playground/playground-recorded-outcome.tsx`
- `console/src/components/playground/playground-response.test.tsx`
- `console/src/components/playground/playground-response.tsx`

### console/src/components/policy/
- `console/src/components/policy/model-allowlist-input.test.tsx`
- `console/src/components/policy/model-allowlist-input.tsx`
- `console/src/components/policy/policy-advanced-section.tsx`
- `console/src/components/policy/policy-form.test.tsx`
- `console/src/components/policy/policy-form.tsx`
- `console/src/components/policy/policy-page.test.tsx`

### console/src/components/shell/
- `console/src/components/shell/operator-shell.tsx`

### console/src/components/tenants/
- `console/src/components/tenants/tenant-editor-drawer.test.tsx`
- `console/src/components/tenants/tenant-editor-drawer.tsx`
- `console/src/components/tenants/tenant-table.test.tsx`
- `console/src/components/tenants/tenant-table.tsx`

### console/src/lib/
- `console/src/lib/admin-api.test.ts`
- `console/src/lib/admin-api.ts`
- `console/src/lib/admin-session-provider.test.tsx`
- `console/src/lib/admin-session-provider.tsx`
- `console/src/lib/freshness.ts`
- `console/src/lib/hosted-contract.test.ts`
- `console/src/lib/hosted-contract.ts`
- `console/src/lib/query-keys.ts`
- `console/src/lib/query-provider.tsx`

### console/src/test/
- `console/src/test/render.tsx`
- `console/src/test/setup.ts`

### deploy/
- `deploy/selfhosted.env.example`

### docs/
- *(23 files: 22 .md, 1 .json)*

### migrations/
- `migrations/env.py`

### migrations/versions/
- `migrations/versions/20260315_0001_governance_baseline.py`
- `migrations/versions/20260321_0002_deployments.py`
- `migrations/versions/20260322_0003_last_seen_at.py`
- `migrations/versions/20260322_0004_credential_raw.py`
- `migrations/versions/20260322_0005_remote_actions.py`
- `migrations/versions/20260326_0006_route_signals.py`
- `migrations/versions/20260328_0007_hard_budget_guardrails.py`
- `migrations/versions/20260328_0008_cache_policy_controls.py`
- `migrations/versions/20260401_0009_calibrated_routing_rollout.py`
- `migrations/versions/20260411_0010_evidence_governance_policy.py`

### scripts/
- `scripts/smoke_openrouter.sh`

### src/nebula/
- `src/nebula/__init__.py`
- `src/nebula/main.py`

### src/nebula/api/
- `src/nebula/api/__init__.py`
- `src/nebula/api/dependencies.py`

### src/nebula/api/routes/
- `src/nebula/api/routes/__init__.py`
- `src/nebula/api/routes/admin.py`
- `src/nebula/api/routes/chat.py`
- `src/nebula/api/routes/embeddings.py`
- `src/nebula/api/routes/enrollment.py`
- `src/nebula/api/routes/heartbeat.py`
- `src/nebula/api/routes/remote_management.py`

### src/nebula/benchmarking/
- `src/nebula/benchmarking/__init__.py`
- `src/nebula/benchmarking/dataset.py`
- `src/nebula/benchmarking/pricing.py`
- `src/nebula/benchmarking/run.py`

### src/nebula/core/
- `src/nebula/core/__init__.py`
- `src/nebula/core/config.py`
- `src/nebula/core/container.py`

### src/nebula/db/
- `src/nebula/db/__init__.py`
- `src/nebula/db/models.py`
- `src/nebula/db/session.py`

### src/nebula/models/
- `src/nebula/models/__init__.py`
- `src/nebula/models/deployment.py`
- `src/nebula/models/governance.py`
- `src/nebula/models/heartbeat.py`
- `src/nebula/models/hosted_contract.py`
- `src/nebula/models/openai.py`

### src/nebula/observability/
- `src/nebula/observability/__init__.py`
- `src/nebula/observability/logging.py`
- `src/nebula/observability/metrics.py`
- `src/nebula/observability/middleware.py`

### src/nebula/providers/
- `src/nebula/providers/__init__.py`
- `src/nebula/providers/base.py`
- `src/nebula/providers/mock_premium.py`
- `src/nebula/providers/ollama.py`
- `src/nebula/providers/openai_compatible.py`

### src/nebula/services/
- `src/nebula/services/__init__.py`
- `src/nebula/services/auth_service.py`
- `src/nebula/services/chat_service.py`
- `src/nebula/services/embeddings_service.py`
- `src/nebula/services/enrollment_service.py`
- `src/nebula/services/gateway_enrollment_service.py`
- `src/nebula/services/governance_store.py`
- `src/nebula/services/heartbeat_ingest_service.py`
- `src/nebula/services/heartbeat_service.py`
- `src/nebula/services/policy_service.py`
- `src/nebula/services/policy_simulation_service.py`
- `src/nebula/services/premium_provider_health_service.py`
- `src/nebula/services/provider_registry.py`
- `src/nebula/services/recommendation_service.py`
- `src/nebula/services/remote_management_service.py`
- `src/nebula/services/retention_lifecycle_service.py`
- `src/nebula/services/router_service.py`
- `src/nebula/services/runtime_health_service.py`
- `src/nebula/services/semantic_cache_service.py`

### tests/
- *(27 files: 27 .py)*
