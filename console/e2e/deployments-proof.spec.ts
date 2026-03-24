import { expect, test } from "@playwright/test";

import { getHostedContractContent } from "../src/lib/hosted-contract";

const { reinforcement } = getHostedContractContent();

const deployments = [
  {
    id: "dep-prod-current",
    display_name: "Production Gateway",
    environment: "production",
    enrollment_state: "active",
    nebula_version: "2.0.0",
    capability_flags: ["remote_credential_rotation"],
    enrolled_at: "2026-03-22T12:00:00Z",
    revoked_at: null,
    unlinked_at: null,
    created_at: "2026-03-22T11:00:00Z",
    updated_at: "2026-03-22T12:10:00Z",
    last_seen_at: "2026-03-22T12:10:00Z",
    freshness_status: "connected",
    freshness_reason: "Heartbeat received recently",
    dependency_summary: { healthy: ["gateway", "qdrant"], degraded: [], unavailable: [] },
    remote_action_summary: { queued: 0, applied: 1, failed: 0, last_action_at: "2026-03-22T12:09:00Z" },
  },
  {
    id: "dep-staging-pending",
    display_name: "Staging Gateway",
    environment: "staging",
    enrollment_state: "pending",
    nebula_version: null,
    capability_flags: [],
    enrolled_at: null,
    revoked_at: null,
    unlinked_at: null,
    created_at: "2026-03-22T10:00:00Z",
    updated_at: "2026-03-22T10:00:00Z",
    last_seen_at: null,
    freshness_status: null,
    freshness_reason: null,
    dependency_summary: null,
    remote_action_summary: { queued: 0, applied: 0, failed: 0, last_action_at: null },
  },
  {
    id: "dep-edge-stale",
    display_name: "Edge Gateway",
    environment: "development",
    enrollment_state: "active",
    nebula_version: "2.0.0",
    capability_flags: ["remote_credential_rotation"],
    enrolled_at: "2026-03-22T08:00:00Z",
    revoked_at: null,
    unlinked_at: null,
    created_at: "2026-03-22T07:00:00Z",
    updated_at: "2026-03-22T08:05:00Z",
    last_seen_at: "2026-03-22T08:05:00Z",
    freshness_status: "stale",
    freshness_reason: "Last report is older than the heartbeat window",
    dependency_summary: { healthy: ["gateway"], degraded: ["postgres"], unavailable: [] },
    remote_action_summary: { queued: 1, applied: 0, failed: 0, last_action_at: "2026-03-22T08:01:00Z" },
  },
  {
    id: "dep-dr-offline",
    display_name: "DR Gateway",
    environment: "production",
    enrollment_state: "active",
    nebula_version: "2.0.0",
    capability_flags: ["remote_credential_rotation"],
    enrolled_at: "2026-03-22T06:00:00Z",
    revoked_at: null,
    unlinked_at: null,
    created_at: "2026-03-22T05:00:00Z",
    updated_at: "2026-03-22T06:05:00Z",
    last_seen_at: "2026-03-22T06:05:00Z",
    freshness_status: "offline",
    freshness_reason: "No current connectivity signal from this deployment",
    dependency_summary: { healthy: [], degraded: [], unavailable: ["gateway", "postgres"] },
    remote_action_summary: { queued: 0, applied: 0, failed: 1, last_action_at: "2026-03-22T06:02:00Z" },
  },
] as const;

const remoteActionHistory = {
  "dep-prod-current": [
    {
      id: "action-applied-1",
      deployment_id: "dep-prod-current",
      action_type: "rotate_deployment_credential",
      status: "applied",
      note: "Rotated after quarterly access review",
      requested_at: "2026-03-22T12:00:00Z",
      expires_at: "2026-03-22T12:15:00Z",
      started_at: "2026-03-22T12:01:00Z",
      finished_at: "2026-03-22T12:02:00Z",
      failure_reason: null,
      failure_detail: null,
      result_credential_prefix: "nbdc_prod_1234",
    },
  ],
  "dep-edge-stale": [
    {
      id: "action-queued-1",
      deployment_id: "dep-edge-stale",
      action_type: "rotate_deployment_credential",
      status: "queued",
      note: "Queued before heartbeat aged out",
      requested_at: "2026-03-22T08:01:00Z",
      expires_at: "2026-03-22T08:16:00Z",
      started_at: null,
      finished_at: null,
      failure_reason: null,
      failure_detail: null,
      result_credential_prefix: null,
    },
  ],
  "dep-dr-offline": [
    {
      id: "action-failed-1",
      deployment_id: "dep-dr-offline",
      action_type: "rotate_deployment_credential",
      status: "failed",
      note: "Rotation failed after connectivity loss",
      requested_at: "2026-03-22T06:00:00Z",
      expires_at: "2026-03-22T06:15:00Z",
      started_at: "2026-03-22T06:01:00Z",
      finished_at: "2026-03-22T06:02:00Z",
      failure_reason: "apply_error",
      failure_detail: "Deployment never acknowledged the rotated credential.",
      result_credential_prefix: null,
    },
  ],
} as const;

test("deployments walkthrough proves mixed fleet posture stays descriptive and bounded", async ({
  page,
}) => {
  await page.route("**/api/admin/session", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ status: "ok" }),
    });
  });

  await page.route("**/api/admin/deployments", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(deployments),
    });
  });

  await page.route("**/api/admin/deployments/*/remote-actions", async (route) => {
    const deploymentId = route.request().url().split("/deployments/")[1]?.split("/")[0] ?? "";
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(remoteActionHistory[deploymentId as keyof typeof remoteActionHistory] ?? []),
    });
  });

  await page.goto("/");
  await page.getByRole("link", { name: "Review hosted trust boundary" }).click();
  await expect(page).toHaveURL(/\/trust-boundary$/);
  await expect(
    page.getByText("Hosted freshness is not local runtime authority."),
  ).toBeVisible();

  await page.goto("/");
  await page.getByLabel("Nebula admin key").fill("nb-admin-valid");
  await page.getByRole("button", { name: "Enter console" }).click();

  await expect(page).toHaveURL(/\/tenants$/);
  await page.getByRole("link", { name: "Deployments" }).click();
  await expect(page).toHaveURL(/\/deployments$/);

  await expect(
    page.getByRole("heading", { name: "Metadata-backed hosted fleet posture" }),
  ).toBeVisible();
  await expect(page.getByText(reinforcement.allowedDescriptiveClaims[0])).toBeVisible();
  await expect(page.getByText(reinforcement.allowedDescriptiveClaims[1])).toBeVisible();
  await expect(page.getByText("4 deployments")).toBeVisible();
  await expect(page.getByText("Linked and current").locator("..").getByText("1")).toBeVisible();
  await expect(page.getByText("Pending enrollment").locator("..").getByText("1")).toBeVisible();
  await expect(page.getByText("Stale or offline visibility").locator("..").getByText("2")).toBeVisible();
  await expect(page.getByText("Bounded actions blocked").locator("..").getByText("3")).toBeVisible();
  await expect(page.getByText(reinforcement.operatorReadingGuidance[1])).toBeVisible();
  await expect(page.getByText(reinforcement.boundedActionPhrasing.description)).toBeVisible();

  const staleRow = page.getByRole("row", { name: /edge gateway dep-edge-stale/i });
  await expect(staleRow.getByText("Stale visibility")).toBeVisible();
  await expect(staleRow.getByText("Rotation blocked")).toBeVisible();
  await expect(
    staleRow.getByText(
      "Hosted posture is stale because the latest deployment report is older than the expected heartbeat window.",
    ),
  ).toBeVisible();

  const offlineRow = page.getByRole("row", { name: /dr gateway dep-dr-offline/i });
  await expect(offlineRow.getByText("Offline visibility")).toBeVisible();
  await expect(offlineRow.getByText("Rotation blocked")).toBeVisible();

  await page.getByText("Production Gateway").click();

  await expect(page.getByRole("heading", { name: "Production Gateway" })).toBeVisible();
  await expect(page.getByText("Deployment detail")).toBeVisible();
  await expect(page.getByText("Heartbeat received recently")).toBeVisible();
  await expect(page.getByText("Dependencies")).toBeVisible();
  await expect(page.getByText("What this deployment shares")).toBeVisible();
  await expect(page.getByText(reinforcement.operatorReadingGuidance[0]).first()).toBeVisible();
  await expect(page.getByText(reinforcement.boundedActionPhrasing.label)).toBeVisible();
  await expect(page.getByText(reinforcement.boundedActionPhrasing.description).first()).toBeVisible();
  await expect(
    page.getByText(
      "Hosted summaries here are metadata-backed and descriptive only. Use local runtime observability to confirm serving-time behavior before treating this deployment as healthy.",
    ),
  ).toBeVisible();
  await expect(page.getByText("Rotated after quarterly access review")).toBeVisible();
  await expect(page.getByText("Credential prefix: nbdc_prod_1234")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Queue rotation" }),
  ).toBeEnabled();

  await expect(
    page.getByText(/request-serving path/i),
  ).toBeVisible();
  await expect(
    page.getByText(/local runtime authority/i),
  ).toBeVisible();
  await expect(page.getByText(/serves traffic/i)).toHaveCount(0);
});
