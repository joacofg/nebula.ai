import { expect, test } from "@playwright/test";

test("operator can submit a playground prompt and see metadata plus recorded outcome", async ({ page }) => {
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

  // The header reads the tenant's target and routing mode from its policy.
  await page.route("**/api/admin/tenants/default/policy", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        routing_mode_default: "auto",
        calibrated_routing_enabled: true,
        allowed_premium_models: ["openai/gpt-4o-mini"],
        semantic_cache_enabled: true,
        semantic_cache_similarity_threshold: 0.9,
        semantic_cache_max_entry_age_hours: 168,
        fallback_enabled: true,
        max_premium_cost_per_request: null,
        hard_budget_limit_usd: null,
        hard_budget_enforcement: null,
        soft_budget_usd: null,
        prompt_capture_enabled: false,
        response_capture_enabled: false,
        evidence_retention_window: "30d",
        metadata_minimization_level: "standard",
        routing_quality_target: 0.9,
      }),
    });
  });

  // The completion waits until the test has seen the pending state.
  let answer: () => void = () => {};
  const answered = new Promise<void>((resolve) => {
    answer = resolve;
  });
  await page.route("**/api/playground/completions", async (route) => {
    expect(route.request().headers()["x-nebula-admin-key"]).toBe("nb-admin-valid");
    await answered;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      headers: {
        "X-Request-ID": "req-play-001",
        "X-Nebula-Tenant-ID": "default",
        "X-Nebula-Route-Target": "premium",
        "X-Nebula-Route-Reason": "direct_premium_model",
        "X-Nebula-Provider": "openai-compatible",
        "X-Nebula-Cache-Hit": "false",
        "X-Nebula-Fallback-Used": "true",
        "X-Nebula-Policy-Mode": "auto",
        "X-Nebula-Policy-Outcome": "allowed",
      },
      body: JSON.stringify({
        id: "chatcmpl-play-001",
        object: "chat.completion",
        created: 1742140800,
        model: "openai/gpt-4o-mini",
        choices: [
          {
            index: 0,
            message: { role: "assistant", content: "Playground response content" },
            finish_reason: "stop",
          },
        ],
        usage: {
          prompt_tokens: 11,
          completion_tokens: 7,
          total_tokens: 18,
        },
        system_fingerprint: null,
        request_id: "req-play-001",
      }),
    });
  });

  await page.route("**/api/admin/usage/ledger?request_id=req-play-001", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([
        {
          request_id: "req-play-001",
          tenant_id: "default",
          requested_model: "openai/gpt-4o-mini",
          final_route_target: "premium",
          final_provider: "openai-compatible",
          fallback_used: true,
          cache_hit: false,
          response_model: "openai/gpt-4o-mini",
          prompt_tokens: 19,
          completion_tokens: 8,
          total_tokens: 27,
          estimated_cost: 0.016,
          latency_ms: 180,
          timestamp: "2026-03-16T22:00:00Z",
          terminal_status: "fallback_completed",
          route_reason: "fallback",
          policy_outcome: "allowed",
        },
      ]),
    });
  });

  await page.goto("/");
  await page.getByLabel("Clave de admin").fill("nb-admin-valid");
  await page.getByRole("button", { name: "Entrar" }).click();

  await expect(page.getByRole("link", { name: "Playground" })).toBeVisible({ timeout: 30_000 });
  await page.getByRole("link", { name: "Playground" }).click();
  await expect(page).toHaveURL(/\/playground$/, { timeout: 30_000 });

  await expect(page.getByRole("combobox").first()).toHaveValue("default");
  const header = page.locator("header");
  await expect(header).toContainText("Default Workspace");
  await expect(header).toContainText("Objetivo0.90");
  await expect(header).toContainText("Modo de ruteoAutomático");

  await page.getByLabel("Prompt").fill("Run the phase 3 playground path.");
  await page.getByRole("button", { name: "Enviar" }).click();

  await expect(page.getByRole("status", { name: "Esperando respuesta…" })).toBeVisible();
  answer();

  await expect(page.getByText("Playground response content")).toBeVisible();
  await expect(page.getByRole("status", { name: "Esperando respuesta…" })).toHaveCount(0);
  const ledger = page.getByRole("region", { name: "Registro en el ledger" });
  await expect(ledger).toBeVisible();
  await expect(ledger.getByRole("group", { name: "Estado" })).toHaveText(/completado con fallback/);
  await expect(ledger.getByRole("group", { name: "Costo estimado" })).toHaveText(/USD 0\.0160/);
  await expect(ledger.getByRole("group", { name: "Proveedor" })).toHaveText(/openai-compatible/);

  await page.getByText("Detalle de la respuesta").click();
  await expect(page.getByRole("group", { name: "Request ID" })).toHaveText(/req-play-001/);
  await expect(page.getByRole("group", { name: "Modo de política" })).toHaveText(/Automático/);
});
