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
    allowed_premium_models: ["openai/gpt-4o-mini"],
    semantic_cache_enabled: true,
    fallback_enabled: true,
    max_premium_cost_per_request: null,
    soft_budget_usd: null,
    prompt_capture_enabled: false,
    response_capture_enabled: false,
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
  await expect(
    page.getByText(
      "Soft budget signal only. Adds policy outcome metadata when exceeded but does not block routing in Phase 4.",
    ),
  ).toBeVisible();
  await expect(runtimeSection.getByText("Soft budget USD")).not.toBeVisible();
  await expect(
    page.getByText(
      "Capture settings are deferred for a future governance/privacy phase and are not editable in Phase 4.",
    ),
  ).toBeVisible();
  await expect(page.getByLabel("Prompt capture enabled")).not.toBeVisible();
  await expect(page.getByLabel("Response capture enabled")).not.toBeVisible();

  await page.selectOption("#routing-mode-default", "premium_only");
  await page.getByRole("checkbox", { name: "Fallback enabled" }).uncheck();
  await page.getByPlaceholder("Add model").fill("openai/gpt-4.5-mini");
  await page.getByRole("button", { name: "Add model" }).click();
  await page.getByRole("button", { name: "Save policy" }).click();

  await page.getByRole("link", { name: "Tenants" }).click();
  await page.getByRole("link", { name: "Policy" }).click();

  await expect(page.locator("#routing-mode-default")).toHaveValue("premium_only");
  await expect(page.getByText("openai/gpt-4.5-mini")).toBeVisible();
});
