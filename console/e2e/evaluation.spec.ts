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
  await page.getByLabel("Nebula admin key").fill("nb-admin-valid");
  await page.getByRole("button", { name: "Enter console" }).click();
  await expect(page.getByRole("link", { name: "Evaluación" })).toBeVisible({ timeout: 30_000 });
  await page.getByRole("link", { name: "Evaluación" }).click();
  await expect(page).toHaveURL(/\/evaluacion$/, { timeout: 30_000 });

  return { writes };
}

async function setSlider(page: Page, value: string) {
  await page.getByRole("slider", { name: "Calidad objetivo" }).fill(value);
}

test("operator moves the quality target and applies it to a tenant", async ({ page }) => {
  const { writes } = await mockConsole(page, routerReplayFixture);

  const costCard = page.getByRole("group", { name: "Costo por 1000 prompts" });
  await expect(costCard).toContainText("$2.500");
  await expect(page.getByRole("img", { name: /Frontera costo\/calidad/ })).toBeVisible();

  await setSlider(page, "0.75");
  await expect(costCard).toContainText("$1.500");
  await expect(page.getByRole("group", { name: "Ahorro vs todo frontier" })).toContainText("−63 %");

  // Reduced motion: the replay waits for the operator instead of autoplaying.
  await expect(page.getByRole("button", { name: "Reproducir" })).toBeVisible();
  await page.getByRole("button", { name: "Paso" }).click();
  await expect(page.getByText("1 / 4 prompts")).toBeVisible();

  await setSlider(page, "0.9");
  await expect(page.getByRole("combobox", { name: "Tenant" })).toHaveValue("default");
  await page.getByRole("button", { name: "Aplicar a este tenant" }).click();

  await expect(page.getByText("Guardado: routing_quality_target = 0.900 en Default Workspace")).toBeVisible();
  expect(writes).toHaveLength(1);
  expect(writes[0]).toMatchObject({ routing_quality_target: 0.9, semantic_cache_similarity_threshold: 0.9 });
});

test("the real replay at 0.95 matches the phase-3 report", async ({ page }) => {
  const replayPath = path.resolve(__dirname, "../../src/nebula/data/router_replay_v1.json");
  const replay = JSON.parse(readFileSync(replayPath, "utf-8"));
  await mockConsole(page, replay);

  // benchmarks/router/v1/report.md, "Default target q ≥ 0.95": cost 1.696, quality 0.957.
  await expect(page.getByRole("group", { name: "Costo por 1000 prompts" })).toContainText("$1.696");
  await expect(page.getByRole("group", { name: "Calidad", exact: true })).toContainText("0.957");
  await expect(page.getByRole("region", { name: "Cifra anidada" })).toContainText("−31 %");

  const shots = process.env.EVAL_SCREENSHOT_DIR;
  if (shots) {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.screenshot({ path: path.join(shots, "evaluacion-full.png"), fullPage: true });
  }
});
