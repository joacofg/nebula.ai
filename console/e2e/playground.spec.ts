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

  await page.route("**/api/playground/completions", async (route) => {
    expect(route.request().headers()["x-nebula-admin-key"]).toBe("nb-admin-valid");
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
  await page.getByLabel("Nebula admin key").fill("nb-admin-valid");
  await page.getByRole("button", { name: "Enter console" }).click();

  await expect(page.getByRole("link", { name: "Playground" })).toBeVisible({ timeout: 30_000 });
  await page.getByRole("link", { name: "Playground" }).click();
  await expect(page).toHaveURL(/\/playground$/, { timeout: 30_000 });

  await expect(page.locator("select")).toHaveValue("default");
  await page.getByLabel("Prompt").fill("Run the phase 3 playground path.");
  await page.getByRole("button", { name: "Run prompt" }).click();

  await expect(page.getByText("Playground response content")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Immediate response evidence" })).toBeVisible();
  await expect(
    page.getByText("These fields describe the live route, policy, and tenant evidence before the ledger finishes recording the same request."),
  ).toBeVisible();
  await expect(
    page.getByText("Immediate response evidence"),
  ).toBeVisible();
  await expect(
    page.getByText("Recorded outcome"),
  ).toBeVisible();
  await expect(page.getByText("Request ID", { exact: true })).toBeVisible();
  await expect(page.getByText("req-play-001")).toBeVisible();
  await expect(
    page.getByText("Persisted ledger evidence for the same request after Nebula records the final route, provider, fallback, and policy outcome."),
  ).toBeVisible();
  await expect(page.getByText("Tenant")).toBeVisible();
  await expect(page.getByText("default")).toBeVisible();
  await expect(page.getByText("Route target")).toBeVisible();
  await expect(page.getByText("premium", { exact: true })).toBeVisible();
  await expect(page.getByText("Route reason")).toBeVisible();
  await expect(page.getByText("direct_premium_model")).toBeVisible();
  await expect(page.getByText("Provider")).toBeVisible();
  await expect(page.getByText("openai-compatible")).toBeVisible();
  await expect(page.getByText("Policy mode")).toBeVisible();
  await expect(page.getByText("auto")).toBeVisible();
  await expect(page.getByText("Policy outcome")).toBeVisible();
  await expect(page.getByText("allowed")).toBeVisible();
  await expect(page.getByText("Fallback used")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Recorded outcome" })).toBeVisible();
  await expect(
    page.getByText("Persisted ledger evidence for the same request after Nebula records the final route, provider, fallback, and policy outcome."),
  ).toBeVisible();
  await expect(page.getByText("fallback_completed")).toBeVisible();
  await expect(page.getByText("fallback", { exact: true })).toBeVisible();
  await expect(page.getByText("Estimated cost")).toBeVisible();
  await expect(page.getByText("$0.0160")).toBeVisible();
});
