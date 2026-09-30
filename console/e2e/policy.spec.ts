import { expect, test } from "@playwright/test";

test.setTimeout(60_000);

test("operator can update tenant policy from the console", async ({ page }) => {
  const tenants = [
    {
      id: "default",
      name: "Default Workspace",
      description: "Bootstrap tenant",
      metadata: {},
      active: true,
      created_at: "2026-03-16T12:00:00Z",
      updated_at: "2026-03-16T12:00:00Z",
    },
  ];

  let policy = {
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
    routing_quality_target: 0.95,
  };

  await page.route("**/api/admin/session", async (route) => {
    await route.fulfill({ status: 200, body: JSON.stringify({ status: "ok" }) });
  });

  await page.route("**/api/admin/tenants", async (route) => {
    await route.fulfill({ status: 200, body: JSON.stringify(tenants) });
  });

  await page.route("**/api/admin/policy/options", async (route) => {
    await route.fulfill({
      status: 200,
      body: JSON.stringify({
        routing_modes: ["auto", "local_only", "premium_only"],
        known_premium_models: ["openai/gpt-4o-mini", "openai/gpt-4.1-mini"],
        default_premium_model: "openai/gpt-4o-mini",
        runtime_enforced_fields: [
          "routing_quality_target",
      "rate_limit_requests_per_minute",
          "routing_mode_default",
          "allowed_premium_models",
          "semantic_cache_enabled",
          "fallback_enabled",
          "max_premium_cost_per_request",
          "hard_budget_limit_usd",
          "hard_budget_enforcement",
        ],
        soft_signal_fields: ["soft_budget_usd"],
        advisory_fields: ["prompt_capture_enabled", "response_capture_enabled"],
      }),
    });
  });

  await page.route("**/api/admin/tenants/default/policy", async (route) => {
    if (route.request().method() === "PUT") {
      policy = route.request().postDataJSON();
      await route.fulfill({ status: 200, body: JSON.stringify(policy) });
      return;
    }
    await route.fulfill({ status: 200, body: JSON.stringify(policy) });
  });

  await page.goto("/");
  await page.getByLabel("Clave de admin").fill("nb-admin-valid");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page.getByRole("link", { name: "Política" })).toBeVisible({ timeout: 30_000 });
  await page.getByRole("link", { name: "Política" }).click();
  await expect(page).toHaveURL(/\/policy$/, { timeout: 30_000 });
  await expect(page.getByRole("heading", { level: 1, name: "Política" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Ruteo" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Límites" })).toBeVisible();
  await expect(page.getByLabel("Presupuesto blando (USD)")).toBeVisible();
  await expect(page.getByLabel("Al agotarse el presupuesto")).toBeDisabled();
  await expect(page.getByText("Primero definir el presupuesto duro.")).toBeVisible();
  await expect(page.getByLabel("Prompt capture enabled")).not.toBeVisible();

  await page.selectOption("#routing-mode-default", "premium_only");
  await page.getByRole("checkbox", { name: "Fallback a premium si falla el local" }).uncheck();
  await page.locator("#hard-budget-limit-usd").fill("25");
  await expect(page.getByLabel("Al agotarse el presupuesto")).toBeEnabled();
  await page.selectOption("#hard-budget-enforcement", "deny");
  await page.getByRole("textbox", { name: "Agregar modelo" }).fill("openai/gpt-4.5-mini");
  await page.getByRole("button", { name: "Agregar", exact: true }).click();
  await expect(page.getByLabel("Objetivo de calidad")).toHaveValue("0.95");
  await page.getByLabel("Objetivo de calidad").fill("0.9");
  await page.getByRole("button", { name: "Guardar política" }).click();

  await page.getByRole("link", { name: "Tenants" }).click();
  await page.getByRole("link", { name: "Política" }).click();

  await expect(page.locator("#routing-mode-default")).toHaveValue("premium_only");
  await expect(page.locator("#hard-budget-limit-usd")).toHaveValue("25");
  await expect(page.locator("#hard-budget-enforcement")).toHaveValue("deny");
  await expect(page.locator("#routing-quality-target")).toHaveValue("0.9");
  await expect(page.getByText("openai/gpt-4.5-mini")).toBeVisible();
});
