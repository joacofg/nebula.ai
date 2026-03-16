import { expect, test } from "@playwright/test";

test.setTimeout(60_000);

test("operator can create, reveal once, and revoke an API key", async ({ page }) => {
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

  const apiKeys = [
    {
      id: "key-1",
      name: "Bootstrap key",
      key_prefix: "nbk_init",
      tenant_id: "default",
      allowed_tenant_ids: ["default"],
      revoked_at: null,
      created_at: "2026-03-16T12:00:00Z",
      updated_at: "2026-03-16T12:00:00Z",
    },
  ];

  await page.route("**/api/admin/session", async (route) => {
    await route.fulfill({ status: 200, body: JSON.stringify({ status: "ok" }) });
  });

  await page.route("**/api/admin/tenants", async (route) => {
    await route.fulfill({ status: 200, body: JSON.stringify(tenants) });
  });

  await page.route("**/api/admin/api-keys*", async (route) => {
    if (route.request().method() === "POST") {
      const payload = route.request().postDataJSON();
      const created = {
        id: "key-2",
        name: payload.name,
        key_prefix: "nbk_new2",
        tenant_id: payload.tenant_id,
        allowed_tenant_ids: payload.allowed_tenant_ids,
        revoked_at: null,
        created_at: "2026-03-16T13:00:00Z",
        updated_at: "2026-03-16T13:00:00Z",
      };
      apiKeys.unshift(created);
      await route.fulfill({
        status: 201,
        body: JSON.stringify({ record: created, api_key: "nbk_secret_123" }),
      });
      return;
    }
    await route.fulfill({ status: 200, body: JSON.stringify(apiKeys) });
  });

  await page.route("**/api/admin/api-keys/*/revoke", async (route) => {
    const apiKey = apiKeys.find((entry) => route.request().url().includes(entry.id));
    if (!apiKey) {
      await route.fulfill({ status: 404, body: JSON.stringify({ detail: "API key not found." }) });
      return;
    }
    apiKey.revoked_at = "2026-03-16T14:00:00Z";
    apiKey.updated_at = "2026-03-16T14:00:00Z";
    await route.fulfill({ status: 200, body: JSON.stringify(apiKey) });
  });

  page.on("dialog", async (dialog) => {
    await dialog.accept();
  });

  await page.goto("/");
  await page.getByLabel("Nebula admin key").fill("nb-admin-valid");
  await page.getByRole("button", { name: "Enter console" }).click();
  await expect(page.getByRole("link", { name: "API Keys" })).toBeVisible({ timeout: 30_000 });
  await page.getByRole("link", { name: "API Keys" }).click();
  await expect(page).toHaveURL(/\/api-keys$/, { timeout: 30_000 });

  await page.locator("header").getByRole("button", { name: "Create API key" }).click();
  await page.getByLabel("name").fill("Tenant-scoped key");
  await page.locator("form").getByRole("button", { name: "Create API key" }).click();

  await expect(page.getByText("This key will not be shown again.")).toBeVisible();
  await page.getByRole("button", { name: "Close" }).click();

  await page.getByRole("button", { name: "Revoke" }).first().click();
  await expect(page.getByText("Revoked", { exact: true })).toBeVisible();
});
