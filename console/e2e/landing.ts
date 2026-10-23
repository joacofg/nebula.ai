import type { Page } from "@playwright/test";

import { routerReplayFixture } from "../src/test/router-replay-fixture";

const LANDING_POLICY = {
  routing_mode_default: "auto",
  calibrated_routing_enabled: true,
  allowed_premium_models: [],
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

/**
 * Signing in lands on Evaluación, which reads the router replay and the selected tenant's policy.
 * A spec about another page mocks them here, before its own routes: Playwright tries the routes
 * registered last first, so a spec's own policy mock still wins, and no request reaches the
 * console's proxy with no gateway behind it (each one would log "the gateway call failed").
 */
export async function mockEvaluationLanding(page: Page) {
  await page.route("**/api/admin/evaluation/router", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(routerReplayFixture) });
  });
  await page.route("**/api/admin/tenants/*/policy", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(LANDING_POLICY) });
  });
}
