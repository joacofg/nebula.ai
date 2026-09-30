import { expect, test } from "@playwright/test";

test("operator can sign in and land on the evaluation page", async ({ page }) => {
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

  await page.getByLabel("Clave de admin").fill("nb-admin-valid");
  await page.getByRole("button", { name: "Entrar" }).click();

  await expect(page).toHaveURL(/\/evaluacion$/);
  await expect(page.getByRole("heading", { level: 1, name: "Evaluación del router" })).toBeVisible();
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
  await page.getByLabel("Clave de admin").fill("nb-admin-valid");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/evaluacion$/);

  await page.reload();

  await expect(page).toHaveURL(/\/\?reason=session-expired$/);
  await expect(page.getByText("La sesión se cerró. Ingresar la clave de admin otra vez.")).toBeVisible();
});
