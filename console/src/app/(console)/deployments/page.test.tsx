import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import DeploymentsPage from "@/app/(console)/deployments/page";
import type { DeploymentRecord, EnrollmentTokenResponse } from "@/lib/admin-api";
import { getHostedContractContent } from "@/lib/hosted-contract";
import { renderWithProviders } from "@/test/render";

const activeDeployment: DeploymentRecord = {
  id: "dep-active",
  display_name: "Production Gateway",
  environment: "production",
  enrollment_state: "active",
  nebula_version: "2.0.0",
  capability_flags: ["remote_credential_rotation"],
  enrolled_at: "2026-03-22T12:00:00Z",
  revoked_at: null,
  unlinked_at: null,
  created_at: "2026-03-22T11:00:00Z",
  updated_at: "2026-03-22T12:00:00Z",
  last_seen_at: "2026-03-22T12:10:00Z",
  freshness_status: "connected",
  freshness_reason: "Heartbeat received recently",
  dependency_summary: { healthy: ["gateway"], degraded: [], unavailable: [] },
  remote_action_summary: { queued: 0, applied: 1, failed: 0, last_action_at: "2026-03-22T12:09:00Z" },
};

const staleDeployment: DeploymentRecord = {
  ...activeDeployment,
  id: "dep-stale",
  display_name: "Stale Gateway",
  freshness_status: "stale",
  freshness_reason: "Last report is older than the heartbeat window",
};

const pendingDeployment: DeploymentRecord = {
  ...activeDeployment,
  id: "dep-pending",
  display_name: "Pending Gateway",
  enrollment_state: "pending",
  freshness_status: null,
  freshness_reason: null,
  last_seen_at: null,
};

const tokenResponse: EnrollmentTokenResponse = {
  token: "nebula-enroll-token",
  expires_at: "2026-03-23T00:00:00Z",
  deployment_id: activeDeployment.id,
};

describe("DeploymentsPage", () => {
  const { reinforcement } = getHostedContractContent();

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === "string" ? input : input.toString();
      const method = init?.method ?? "GET";

      if (url === "/api/admin/deployments" && method === "GET") {
        return Promise.resolve(
          new Response(JSON.stringify([activeDeployment, staleDeployment, pendingDeployment]), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        );
      }

      if (
        url === `/api/admin/deployments/${activeDeployment.id}/remote-actions` &&
        method === "GET"
      ) {
        return Promise.resolve(
          new Response(JSON.stringify([]), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        );
      }

      if (
        url === `/api/admin/deployments/${activeDeployment.id}/enrollment-token` &&
        method === "POST"
      ) {
        return Promise.resolve(
          new Response(JSON.stringify(tokenResponse), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        );
      }

      return Promise.reject(new Error(`Unhandled fetch: ${method} ${url}`));
    }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("composes the hosted walkthrough from fleet summary into deployment detail trust guidance", async () => {
    renderWithProviders(<DeploymentsPage />, { adminKey: "nebula-admin-key" });

    expect(screen.getByRole("heading", { name: "Deployment management" })).toBeInTheDocument();
    expect(
      screen.getByText(
        `${reinforcement.operatorReadingGuidance[2]} ${reinforcement.allowedDescriptiveClaims[4]}`,
      ),
    ).toBeInTheDocument();

    expect(
      await screen.findByRole("heading", { name: "Metadata-backed hosted fleet posture" }),
    ).toBeInTheDocument();
    expect(screen.getByText(reinforcement.allowedDescriptiveClaims[0])).toBeInTheDocument();
    expect(screen.getByText(reinforcement.allowedDescriptiveClaims[1])).toBeInTheDocument();
    expect(screen.getByText(reinforcement.operatorReadingGuidance[1])).toBeInTheDocument();
    expect(screen.getByText(reinforcement.boundedActionPhrasing.description)).toBeInTheDocument();

    const staleRow = screen.getByRole("row", { name: /stale gateway dep-stale/i });
    expect(within(staleRow).getByText("Stale visibility")).toBeInTheDocument();
    expect(within(staleRow).getByText("Rotation blocked")).toBeInTheDocument();
    expect(
      within(staleRow).getByText(
        "Hosted posture is stale because the latest deployment report is older than the expected heartbeat window.",
      ),
    ).toBeInTheDocument();

    await userEvent.click(screen.getByText("Production Gateway"));

    expect(await screen.findByRole("heading", { name: "Production Gateway" })).toBeInTheDocument();
    expect(screen.getByText("Deployment detail")).toBeInTheDocument();
    expect(screen.getByText("What this deployment shares")).toBeInTheDocument();
    expect(screen.getAllByText(reinforcement.operatorReadingGuidance[0]).length).toBeGreaterThan(0);
    expect(screen.getAllByText(reinforcement.boundedActionPhrasing.description).length).toBeGreaterThan(0);
    expect(
      screen.getByText(
        /Hosted summaries here are metadata-backed and descriptive only\./,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Use local runtime observability to confirm serving-time behavior/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/hosted plane serves traffic/i)).not.toBeInTheDocument();
  });

  it("keeps the create state as a bounded console entrypoint while loading real fleet posture", async () => {
    renderWithProviders(<DeploymentsPage />, { adminKey: "nebula-admin-key" });

    expect(screen.getByRole("button", { name: "Create deployment slot" })).toBeInTheDocument();
    expect(
      await screen.findByText(/Reserve a named slot in the hosted inventory\./),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/The hosted plane receives metadata only — no prompts, responses, or provider credentials\./),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("3 deployments")).toBeInTheDocument();
    });
  });
});
