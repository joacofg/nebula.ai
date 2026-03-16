import { expect, test } from "@playwright/test";

test("operator can submit a playground prompt and see the request id", async ({ page }) => {
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
        "X-Nebula-Provider": "mock-premium",
        "X-Nebula-Cache-Hit": "false",
        "X-Nebula-Fallback-Used": "false",
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
            message: {
              role: "assistant",
              content: "Playground response content",
            },
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
  await expect(page.getByText("Request ID", { exact: true })).toBeVisible();
  await expect(page.getByText("req-play-001")).toBeVisible();
});
