import { readFileSync } from "node:fs";
import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

import { routerReplayFixture } from "../src/test/router-replay-fixture";

test.setTimeout(60_000);

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

async function mockConsole(page: Page, replay: unknown) {
  let policy: Record<string, unknown> = {
    routing_mode_default: "auto",
    calibrated_routing_enabled: true,
    allowed_premium_models: ["openai/gpt-4.1"],
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
  const writes: Record<string, unknown>[] = [];
  // Keeps the replay feed paused so the assertions below are deterministic.
  await page.emulateMedia({ reducedMotion: "reduce" });

  await page.route("**/api/admin/session", async (route) => {
    await route.fulfill({ status: 200, body: JSON.stringify({ status: "ok" }) });
  });
  await page.route("**/api/admin/tenants", async (route) => {
    await route.fulfill({ status: 200, body: JSON.stringify(tenants) });
  });
  await page.route("**/api/admin/evaluation/router", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(replay) });
  });
  await page.route("**/api/admin/tenants/default/policy", async (route) => {
    if (route.request().method() === "PUT") {
      policy = route.request().postDataJSON();
      writes.push(policy);
    }
    await route.fulfill({ status: 200, body: JSON.stringify(policy) });
  });

  await page.goto("/");
  await page.getByLabel("Clave de admin").fill("nb-admin-valid");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page.getByRole("link", { name: "Evaluación" })).toBeVisible({ timeout: 30_000 });
  await page.getByRole("link", { name: "Evaluación" }).click();
  await expect(page).toHaveURL(/\/evaluacion$/, { timeout: 30_000 });

  return { writes };
}

async function setSlider(page: Page, value: string) {
  await page.getByRole("slider", { name: "Calidad objetivo" }).fill(value);
}

/** The slider panel's readings: the readout that leads with the saving headline. */
function sliderReadout(page: Page) {
  return page.locator("dl").filter({ has: page.getByRole("group", { name: "Ahorro vs todo frontier" }) });
}

/** The replay's running readings, which carry the same cost label. */
function replayReadout(page: Page) {
  return page.getByRole("region", { name: /Replay acelerado/ });
}

test("operator moves the quality target and applies it to a tenant", async ({ page }) => {
  const { writes } = await mockConsole(page, routerReplayFixture);

  const costCard = sliderReadout(page).getByRole("group", { name: "Costo por 1000 pedidos" });
  // The slider opens at the tenant's current target.
  await expect(page.getByRole("slider", { name: "Calidad objetivo" })).toHaveValue("0.95");
  await expect(page.getByText("Objetivo actual 0.95")).toBeVisible();
  await expect(costCard).toContainText("USD 2.50");
  await expect(page.getByRole("group", { name: /Frontera costo–calidad/ })).toBeVisible();

  await setSlider(page, "0.75");
  await expect(costCard).toContainText("USD 1.50");
  await expect(page.getByRole("group", { name: "Ahorro vs todo frontier" })).toContainText("63 %");

  // Reduced motion: the replay waits for the operator instead of autoplaying.
  const replayQuality = replayReadout(page).getByRole("group", { name: "Calidad acumulada" });
  await expect(replayQuality).toContainText("—");
  await expect(page.getByRole("button", { name: "Reproducir" })).toBeVisible();
  await page.getByRole("button", { name: "Paso" }).click();
  await expect(page.getByText("1 / 4 pedidos")).toBeVisible();
  await expect(replayQuality).not.toContainText("—");
  await expect(replayReadout(page).getByRole("group", { name: "Costo por 1000 pedidos" })).toContainText("USD");

  await setSlider(page, "0.9");
  await expect(page.getByRole("combobox", { name: "Tenant" })).toHaveValue("default");
  await page.getByRole("button", { name: "Aplicar al tenant" }).click();

  await expect(page.getByText("Objetivo 0.90 guardado en Default Workspace.")).toBeVisible();
  expect(writes).toHaveLength(1);
  expect(writes[0]).toMatchObject({ routing_quality_target: 0.9, semantic_cache_similarity_threshold: 0.9 });
  await expect(page.getByText("Objetivo actual 0.90")).toBeVisible();

  // The success line belongs to the saved value: moving the slider again clears it.
  await setSlider(page, "0.95");
  await expect(page.getByText("Objetivo 0.90 guardado en Default Workspace.")).toHaveCount(0);
});

test("the real replay at 0.95 matches the phase-3 report", async ({ page }) => {
  const replayPath = path.resolve(__dirname, "../../src/nebula/data/router_replay_v1.json");
  const replay = JSON.parse(readFileSync(replayPath, "utf-8"));
  await mockConsole(page, replay);

  // benchmarks/router/v1/report.md, "Default target q ≥ 0.95": cost 1.696, quality 0.957.
  await expect(sliderReadout(page).getByRole("group", { name: "Costo por 1000 pedidos" })).toContainText("USD 1.70");
  await expect(page.getByRole("group", { name: "Calidad medida" })).toContainText("0.957");
  await expect(page.getByRole("table", { name: "Características a calidad objetivo 0.95" })).toContainText("31 %");

  const shots = process.env.EVAL_SCREENSHOT_DIR;
  if (shots) {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.screenshot({ path: path.join(shots, "evaluacion-full.png"), fullPage: true });
  }
});
