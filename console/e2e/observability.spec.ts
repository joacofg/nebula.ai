import { expect, test } from "@playwright/test";

test("operator can filter the ledger and inspect dependency health", async ({ page }) => {
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
        {
          id: "team-b",
          name: "Team B",
          description: "Second tenant",
          metadata: {},
          active: true,
          created_at: "2026-03-16T12:10:00Z",
          updated_at: "2026-03-16T12:10:00Z",
        },
      ]),
    });
  });

  await page.route("**/api/admin/usage/ledger**", async (route) => {
    const url = new URL(route.request().url());
    const tenantId = url.searchParams.get("tenant_id");
    const rows =
      tenantId === "team-b"
        ? [
            {
              request_id: "req-team-b",
              tenant_id: "team-b",
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
            },
          ]
        : [
            {
              request_id: "req-default",
              tenant_id: "default",
              requested_model: "llama3.2:3b",
              final_route_target: "local",
              final_provider: "ollama",
              fallback_used: false,
              cache_hit: false,
              response_model: "llama3.2:3b",
              prompt_tokens: 14,
              completion_tokens: 7,
              total_tokens: 21,
              estimated_cost: 0,
              latency_ms: 160,
              timestamp: "2026-03-16T21:00:00Z",
              terminal_status: "completed",
              route_reason: "local_model",
              policy_outcome: "allowed",
            },
          ];

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(rows),
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
          gateway: {
            status: "ready",
            required: true,
            detail: "FastAPI application is running.",
          },
          governance_store: {
            status: "ready",
            required: true,
            detail: "Governance store is connected and schema is present.",
          },
          semantic_cache: {
            status: "ready",
            required: false,
            detail: "Qdrant reachable.",
          },
          local_ollama: {
            status: "ready",
            required: false,
            detail: "Ollama reachable.",
          },
          premium_provider: {
            status: "degraded",
            required: false,
            detail: "Premium provider probe timed out.",
          },
        },
      }),
    });
  });

  await page.goto("/");
  await page.getByLabel("Nebula admin key").fill("nb-admin-valid");
  await page.getByRole("button", { name: "Enter console" }).click();

  await expect(page.getByRole("link", { name: "Observability" })).toBeVisible({ timeout: 30_000 });
  await page.getByRole("link", { name: "Observability" }).click();
  await expect(page).toHaveURL(/\/observability$/, { timeout: 30_000 });

  await expect(page.getByRole("heading", { name: "Usage ledger" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Dependency health" })).toBeVisible();

  await page.getByRole("combobox", { name: "Tenant" }).selectOption("team-b");
  await expect(page.getByRole("cell", { name: "team-b" })).toBeVisible();
  await expect(page.getByText("premium_provider")).toBeVisible();
  await expect(page.getByText("degraded")).toBeVisible();
  await expect(
    page.getByText("Optional dependency degradation does not block gateway readiness."),
  ).toBeVisible();
});
