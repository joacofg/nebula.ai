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
  await page.getByLabel("Nebula admin key").fill("nb-admin-valid");
  await page.getByRole("button", { name: "Enter console" }).click();
  await expect(page.getByRole("link", { name: "Policy" })).toBeVisible({ timeout: 30_000 });
  await page.getByRole("link", { name: "Policy" }).click();
  await expect(page).toHaveURL(/\/policy$/, { timeout: 30_000 });
  const runtimeHeading = page.getByRole("heading", { name: "Runtime-enforced controls" });
  const runtimeSection = runtimeHeading.locator("xpath=ancestor::section[1]");
  await expect(runtimeHeading).toBeVisible();
  await expect(page.getByText("Applies in live request evaluation")).toBeVisible();
  await expect(
    page.getByText(
      "These controls change live routing behavior. Hard budget settings are cumulative tenant spend guardrails, not advisory reporting thresholds.",
    ),
  ).toBeVisible();
  await expect(
    page.getByText(
      "When the hard cumulative budget is exhausted, Nebula either downgrades compatible auto-routed traffic to local or denies premium routing, depending on the enforcement mode below.",
    ),
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: "Soft budget advisory" })).toBeVisible();
  await expect(
    page.getByText(
      "Advisory only. Exceeding this threshold adds operator-visible policy outcome metadata, but it does not block, downgrade, or deny routing.",
    ),
  ).toBeVisible();
  await expect(runtimeSection.getByText("Soft budget USD")).not.toBeVisible();
  await expect(page.getByLabel("Hard budget enforcement")).toBeDisabled();
  await expect(
    page.getByText("Set a hard cumulative budget limit first to activate this enforcement choice."),
  ).toBeVisible();
  await expect(page.getByLabel("Prompt capture enabled")).not.toBeVisible();
  await expect(page.getByLabel("Response capture enabled")).not.toBeVisible();

  await page.selectOption("#routing-mode-default", "premium_only");
  await page.getByRole("checkbox", { name: "Fallback enabled" }).uncheck();
  await page.locator("#hard-budget-limit-usd").fill("25");
  await expect(page.getByLabel("Hard budget enforcement")).toBeEnabled();
  await page.selectOption("#hard-budget-enforcement", "deny");
  await page.getByPlaceholder("Add model").fill("openai/gpt-4.5-mini");
  await page.getByRole("button", { name: "Add model" }).click();
  await expect(page.getByLabel("Routing quality target")).toHaveValue("0.95");
  await page.getByLabel("Routing quality target").fill("0.9");
  await page.getByRole("button", { name: "Save policy" }).click();

  await page.getByRole("link", { name: "Tenants" }).click();
  await page.getByRole("link", { name: "Policy" }).click();

  await expect(page.locator("#routing-mode-default")).toHaveValue("premium_only");
  await expect(page.locator("#hard-budget-limit-usd")).toHaveValue("25");
  await expect(page.locator("#hard-budget-enforcement")).toHaveValue("deny");
  await expect(page.locator("#routing-quality-target")).toHaveValue("0.9");
  await expect(page.getByText("openai/gpt-4.5-mini")).toBeVisible();
});
