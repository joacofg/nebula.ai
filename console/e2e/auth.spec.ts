import { expect, test } from "@playwright/test";

test("operator can sign in and land on tenants", async ({ page }) => {
  await page.route("**/api/admin/tenants", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
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

  await page.route("**/api/admin/session", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ status: "ok" }),
    });
  });

  await page.goto("/");

  await page.getByLabel("Nebula admin key").fill("nb-admin-valid");
  await page.getByRole("button", { name: "Enter console" }).click();

  await expect(page).toHaveURL(/\/tenants$/);
  await expect(page.getByRole("heading", { name: "Tenant operations" })).toBeVisible();
});

test("refresh clears the in-memory admin session", async ({ page }) => {
  await page.route("**/api/admin/tenants", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
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

  await page.route("**/api/admin/session", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ status: "ok" }),
    });
  });

  await page.goto("/");
  await page.getByLabel("Nebula admin key").fill("nb-admin-valid");
  await page.getByRole("button", { name: "Enter console" }).click();
  await expect(page).toHaveURL(/\/tenants$/);

  await page.reload();

  await expect(page).toHaveURL(/\/\?reason=session-expired$/);
  await expect(page.getByText("Enter the Nebula admin key again")).toBeVisible();
});
