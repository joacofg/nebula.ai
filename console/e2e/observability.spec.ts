import { expect, test } from "@playwright/test";

test("operator can inspect request-first outage and recovery truth on observability", async ({ page }) => {
  await page.route("**/api/admin/session", async (route) => {
    await route.fulfill({ status: 200, body: JSON.stringify({ status: "ok" }) });
  });

  await page.route("**/api/admin/tenants", async (route) => {
    await route.fulfill({
      status: 200,
      body: JSON.stringify([
        {
          id: "default",
          name: "Default Workspace",
          description: "Bootstrap tenant",
          metadata: {},
          active: true,
          created_at: "2026-03-16T12:00:00Z",
          updated_at: "2026-03-16T12:00:00Z",
        },
      ]),
    });
  });

  await page.route("**/api/admin/usage/ledger**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([
        {
          request_id: "req-governance-001",
          tenant_id: "default",
          requested_model: "openai/gpt-4o-mini",
          final_route_target: "premium",
          final_provider: "openai-compatible",
          fallback_used: false,
          cache_hit: false,
          response_model: "openai/gpt-4o-mini",
          prompt_tokens: 22,
          completion_tokens: 10,
          total_tokens: 32,
          estimated_cost: 0.021,
          latency_ms: 210,
          timestamp: "2026-03-16T22:00:00Z",
          terminal_status: "completed",
          route_reason: "direct_premium_model",
          policy_outcome: "allowed",
          route_signals: {
            route_mode: "calibrated",
            calibrated_routing: true,
            degraded_routing: false,
            route_score: 0.88,
            token_count: 32,
            complexity_tier: "high",
            keyword_match: true,
            model_constraint: false,
            budget_proximity: 0.2,
            score_components: {
              total_score: 0.88,
              token_score: 0.63,
              keyword_bonus: 0.15,
              policy_bonus: 0.1,
              budget_penalty: 0,
            },
          },
          message_type: "chat",
          evidence_retention_window: "30d",
          evidence_expires_at: "2026-04-15T22:00:00Z",
          metadata_minimization_level: "standard",
          metadata_fields_suppressed: [],
          governance_source: "tenant_policy",
        },
      ]),
    });
  });

  await page.route("**/api/admin/tenants/default/recommendations", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        tenant_id: "default",
        generated_at: "2026-03-27T18:00:00Z",
        window_requests_evaluated: 24,
        calibration_summary: {
          tenant_id: "default",
          scope: "tenant",
          state: "sufficient",
          state_reason: "Recent eligible calibrated rows meet the tenant sufficiency threshold.",
          generated_at: "2026-03-27T18:00:00Z",
          latest_eligible_request_at: "2026-03-27T17:15:00Z",
          latest_any_request_at: "2026-03-27T17:15:00Z",
          eligible_request_count: 12,
          sufficient_request_count: 12,
          thin_request_threshold: 5,
          staleness_threshold_hours: 24,
          excluded_request_count: 1,
          gated_request_count: 0,
          degraded_request_count: 1,
          excluded_reasons: [{ reason: "policy_forced_route", count: 1 }],
          gated_reasons: [],
          degraded_reasons: [{ reason: "missing_route_signals", count: 1 }],
        },
        recommendations: [
          {
            code: "cache-tighten-threshold",
            title: "Tighten cache similarity threshold",
            priority: 1,
            category: "cache",
            summary: "Recent ledger-backed traffic shows reuse with mixed downstream outcomes.",
            recommended_action: "Raise the similarity threshold in policy preview before saving.",
            evidence: [
              { label: "Requests evaluated", value: "24" },
              { label: "Estimated hit rate", value: "42%" },
            ],
          },
        ],
        cache_summary: {
          enabled: true,
          similarity_threshold: 0.82,
          max_entry_age_hours: 48,
          runtime_status: "degraded",
          runtime_detail: "Qdrant latency is elevated but cache lookups still succeed.",
          estimated_hit_rate: 0.42,
          avoided_premium_cost_usd: 1.275,
          insights: [
            {
              code: "cache-health-watch",
              title: "Watch degraded cache runtime",
              level: "notice",
              summary: "Recent cache reuse remains valuable, but degraded runtime may reduce consistency.",
              evidence: [{ label: "Runtime status", value: "degraded" }],
            },
          ],
        },
      }),
    });
  });

  await page.route("**/api/runtime/health", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "degraded",
        runtime_profile: "premium_first",
        dependencies: {
          governance_store: {
            status: "not_ready",
            required: true,
            detail: "Governance queries failed; requests are blocked fail-closed.",
            dependency_class: "serving_critical",
            lifecycle_state: "not_ready",
            serving_effect: "fail_closed",
            reason_code: "governance_query_failed",
            recovering: false,
            enabled: true,
            last_failure_at: "2026-04-12T01:00:00Z",
          },
          semantic_cache: {
            status: "degraded",
            required: false,
            detail: "Semantic cache unavailable; requests continue without cache hits.",
            dependency_class: "serving_optional",
            lifecycle_state: "degraded",
            serving_effect: "continuity_limited",
            reason_code: "semantic_cache_unavailable",
            recovering: false,
            enabled: true,
            last_failure_at: "2026-04-12T00:55:00Z",
          },
          premium_provider: {
            status: "recovering",
            required: false,
            detail: "Premium provider connectivity restored; recovery checks are still running.",
            dependency_class: "serving_optional",
            lifecycle_state: "recovering",
            serving_effect: "continuity_limited",
            reason_code: "premium_provider_recovered",
            recovering: true,
            enabled: true,
            last_failure_at: "2026-04-12T00:55:00Z",
            last_recovery_at: "2026-04-12T01:03:00Z",
          },
        },
      }),
    });
  });

  await page.goto("/");
  await page.getByLabel("Clave de admin").fill("nb-admin-valid");
  await page.getByRole("button", { name: "Entrar" }).click();

  await expect(page.getByRole("link", { name: "Observabilidad" })).toBeVisible({ timeout: 30_000 });
  await page.getByRole("link", { name: "Observabilidad" }).click();
  await expect(page).toHaveURL(/\/observability$/, { timeout: 30_000 });

  await expect(page.getByRole("heading", { level: 1, name: "Observabilidad" })).toBeVisible();
  const ledger = page.getByRole("table", { name: "Ledger de pedidos" });
  await expect(ledger.getByRole("row", { name: /req-governance-001/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Pedido/ })).toContainText("req-gove");

  await page.getByRole("tab", { name: "Dependencias" }).click();
  const deps = page.getByRole("tabpanel");
  await expect(deps.getByText("governance_store", { exact: true })).toBeVisible();
  await expect(deps.getByText("semantic_cache", { exact: true })).toBeVisible();
  await expect(deps.getByText("premium_provider", { exact: true })).toBeVisible();
  await expect(deps.getByText("serving critical")).toBeVisible();
  await expect(deps.getByText("fail closed")).toBeVisible();
  await expect(deps.getByText("governance query failed")).toBeVisible();
  await expect(deps.getByText("premium provider recovered")).toBeVisible();
  await expect(deps.getByText("2026-04-12T01:03:00Z")).toBeVisible();
  await expect(page.getByText(/dashboard/i)).toHaveCount(0);
});