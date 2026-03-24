import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { getBoundedActionAvailability } from "@/components/deployments/fleet-posture";
import { RemoteActionCard } from "@/components/deployments/remote-action-card";
import type { DeploymentRecord } from "@/lib/admin-api";
import { getHostedContractContent } from "@/lib/hosted-contract";
import { renderWithProviders } from "@/test/render";

const baseDeployment: DeploymentRecord = {
  id: "dep-1",
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
  remote_action_summary: { queued: 0, applied: 0, failed: 0, last_action_at: null },
};

function renderCard(deployment: DeploymentRecord = baseDeployment) {
  renderWithProviders(<RemoteActionCard deployment={deployment} />, {
    adminKey: "nebula-admin-key",
  });
}

describe("RemoteActionCard", () => {
  const { reinforcement } = getHostedContractContent();

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders bounded hosted wording without implying broader control", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify([]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    renderCard();

    expect(await screen.findByText("No remote actions recorded yet.")).toBeInTheDocument();
    expect(screen.getByText(reinforcement.boundedActionPhrasing.description)).toBeInTheDocument();
    expect(
      screen.getByText(/Hosted summaries here are metadata-backed and descriptive only\./),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Use local runtime observability to confirm serving-time behavior/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/broader remote control/i)).not.toBeInTheDocument();
  });

  it("requires a 1-280 character note and only queues after confirmation", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify([]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            id: "action-1",
            deployment_id: "dep-1",
            action_type: "rotate_deployment_credential",
            status: "queued",
            note: "Rotate after audit",
            requested_at: "2026-03-22T12:12:00Z",
            expires_at: "2026-03-22T12:27:00Z",
            started_at: null,
            finished_at: null,
            failure_reason: null,
            failure_detail: null,
            result_credential_prefix: null,
          }),
          {
            status: 201,
            headers: { "Content-Type": "application/json" },
          },
        ),
      );
    const confirmMock = vi.fn().mockReturnValueOnce(false).mockReturnValueOnce(true);
    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("confirm", confirmMock);

    renderCard();

    await screen.findByText("No remote actions recorded yet.");

    await userEvent.click(screen.getByRole("button", { name: "Queue rotation" }));
    expect(screen.getByText("Enter a note between 1 and 280 characters.")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);

    await userEvent.type(screen.getByLabelText("Rotation note"), "Rotate after audit");
    await userEvent.click(screen.getByRole("button", { name: "Queue rotation" }));

    expect(confirmMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(1);

    await userEvent.click(screen.getByRole("button", { name: "Queue rotation" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(2);
    });
    expect(confirmMock).toHaveBeenCalledTimes(2);
    expect(screen.getByText("Rotate after audit", { selector: "p" })).toBeInTheDocument();
  });

  it("fails closed for stale, offline, revoked, unlinked, and unsupported deployments", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const cases: Array<{ deployment: DeploymentRecord; reason: string; status: ReturnType<typeof getBoundedActionAvailability>["status"] }> = [
      {
        deployment: { ...baseDeployment, freshness_status: "stale" },
        reason: "Rotation is blocked because the deployment is stale and no longer trusted for remote changes.",
        status: "blocked",
      },
      {
        deployment: { ...baseDeployment, freshness_status: "offline" },
        reason: "Rotation is blocked because the deployment is offline and cannot confirm credential handoff.",
        status: "blocked",
      },
      {
        deployment: { ...baseDeployment, enrollment_state: "revoked" },
        reason: "Rotation is unavailable because this hosted link has been revoked.",
        status: "unavailable",
      },
      {
        deployment: { ...baseDeployment, enrollment_state: "unlinked" },
        reason: "Rotation is unavailable because this deployment is no longer linked.",
        status: "unavailable",
      },
      {
        deployment: { ...baseDeployment, capability_flags: [] },
        reason:
          "Rotation is unavailable because this deployment did not advertise remote credential rotation support.",
        status: "unavailable",
      },
    ];

    for (const testCase of cases) {
      expect(getBoundedActionAvailability(testCase.deployment).status).toBe(testCase.status);
      expect(getBoundedActionAvailability(testCase.deployment).disabledReason).toBe(testCase.reason);
      const { unmount } = renderWithProviders(<RemoteActionCard deployment={testCase.deployment} />, {
        adminKey: "nebula-admin-key",
      });
      expect(await screen.findByText(testCase.reason)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Queue rotation" })).toBeDisabled();
      unmount();
    }
  });

  it("renders recent history with status, note, timestamps, failure reason, and credential prefix", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify([
            {
              id: "action-newest",
              deployment_id: "dep-1",
              action_type: "rotate_deployment_credential",
              status: "failed",
              note: "Rotation failed after local validation",
              requested_at: "2026-03-22T12:20:00Z",
              expires_at: "2026-03-22T12:35:00Z",
              started_at: "2026-03-22T12:21:00Z",
              finished_at: "2026-03-22T12:22:00Z",
              failure_reason: "expired",
              failure_detail: "Remote action expired before completion.",
              result_credential_prefix: null,
            },
            {
              id: "action-older",
              deployment_id: "dep-1",
              action_type: "rotate_deployment_credential",
              status: "applied",
              note: "Rotation applied cleanly",
              requested_at: "2026-03-22T12:00:00Z",
              expires_at: "2026-03-22T12:15:00Z",
              started_at: "2026-03-22T12:01:00Z",
              finished_at: "2026-03-22T12:02:00Z",
              failure_reason: null,
              failure_detail: null,
              result_credential_prefix: "nbdc_abcd1234",
            },
          ]),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
      ),
    );

    renderCard();

    expect(await screen.findByText("Rotation failed after local validation")).toBeInTheDocument();
    expect(screen.getByText("Rotation applied cleanly")).toBeInTheDocument();
    expect(screen.getByText("Failure reason: expired")).toBeInTheDocument();
    expect(screen.getByText("Credential prefix: nbdc_abcd1234")).toBeInTheDocument();

    const historyNotes = screen.getAllByText(/Rotation (failed|applied)/);
    expect(historyNotes[0]).toHaveTextContent("Rotation failed after local validation");
    expect(historyNotes[1]).toHaveTextContent("Rotation applied cleanly");
  });
});
