import { expect, test } from "@playwright/test";

test("operator can create, edit, and keep an inactive tenant visible", async ({ page }) => {
  const tenants = [
    {
      id: "default",
      name: "Default Workspace",
      description: "Bootstrap tenant",
      metadata: { bootstrap: true },
      active: true,
      created_at: "2026-03-16T12:00:00Z",
      updated_at: "2026-03-16T12:00:00Z",
    },
  ];

  await page.route("**/api/admin/session", async (route) => {
    await route.fulfill({ status: 200, body: JSON.stringify({ status: "ok" }) });
  });

  await page.route("**/api/admin/tenants", async (route) => {
    if (route.request().method() === "POST") {
      const payload = route.request().postDataJSON();
      tenants.unshift({
        ...payload,
        description: payload.description || "",
        created_at: "2026-03-16T13:00:00Z",
        updated_at: "2026-03-16T13:00:00Z",
      });
      await route.fulfill({ status: 201, body: JSON.stringify(tenants[0]) });
      return;
    }
    await route.fulfill({ status: 200, body: JSON.stringify(tenants) });
  });

  await page.route("**/api/admin/tenants/*", async (route) => {
    const tenantId = route.request().url().split("/").pop();
    const payload = route.request().postDataJSON();
    const tenant = tenants.find((item) => item.id === tenantId);
    if (!tenant) {
      await route.fulfill({ status: 404, body: JSON.stringify({ detail: "Tenant not found." }) });
      return;
    }
    Object.assign(tenant, payload, { updated_at: "2026-03-16T14:00:00Z" });
    await route.fulfill({ status: 200, body: JSON.stringify(tenant) });
  });

  await page.goto("/");
  await page.getByLabel("Clave de admin").fill("nb-admin-valid");
  await page.getByRole("button", { name: "Entrar" }).click();

  await expect(page).toHaveURL(/\/evaluacion$/, { timeout: 30_000 });
  await page.getByRole("link", { name: "Tenants" }).click();
  await expect(page).toHaveURL(/\/tenants$/, { timeout: 30_000 });
  await page.locator("header").getByRole("button", { name: "Crear tenant" }).click();
  await page.getByLabel("Id", { exact: true }).fill("team-b");
  await page.getByLabel("Nombre").fill("Team B");
  await page.getByLabel("Descripción").fill("Created from tenants.spec.ts");
  await page.locator("form").getByRole("button", { name: "Crear tenant" }).click();

  await expect(page.getByRole("heading", { name: "Editar Team B" })).toBeVisible();

  await page.locator("tbody").getByText("Team B", { exact: true }).click();
  await page.getByLabel("Descripción").fill("Updated description");
  await page.getByRole("checkbox", { name: "Activo" }).uncheck();
  await page.getByRole("button", { name: "Guardar tenant" }).click();

  await page.getByRole("combobox").selectOption("inactive");
  await expect(page.getByText("Updated description")).toBeVisible();
});
