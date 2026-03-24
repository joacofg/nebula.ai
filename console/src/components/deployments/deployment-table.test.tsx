import { describe, it, expect, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { DeploymentTable } from "./deployment-table";
import type { DeploymentRecord } from "@/lib/admin-api";

const baseDeployment: DeploymentRecord = {
  id: "dep-1",
  display_name: "Production Gateway",
  environment: "production",
  enrollment_state: "active",
  nebula_version: "1.2.0",
  capability_flags: ["semantic_cache", "remote_credential_rotation"],
  enrolled_at: "2026-03-20T00:00:00Z",
  revoked_at: null,
  unlinked_at: null,
  created_at: "2026-03-19T00:00:00Z",
  updated_at: "2026-03-20T00:00:00Z",
  last_seen_at: "2026-03-22T12:00:00Z",
  freshness_status: "connected",
  freshness_reason: "Last heartbeat 3 minutes ago",
  dependency_summary: { healthy: ["gateway"], degraded: [], unavailable: [] },
  remote_action_summary: { queued: 0, applied: 1, failed: 0, last_action_at: null },
};

function makeDeployment(overrides: Partial<DeploymentRecord>): DeploymentRecord {
  return {
    ...baseDeployment,
    ...overrides,
  };
}

describe("DeploymentTable", () => {
  it("renders Posture, Version, and Last Seen column headers", () => {
    render(
      <DeploymentTable
        deployments={[baseDeployment]}
        selectedDeploymentId={null}
        onSelectDeployment={vi.fn()}
      />,
    );

    expect(screen.getByText("Posture")).toBeDefined();
    expect(screen.getByText("Version")).toBeDefined();
    expect(screen.getByText("Last Seen")).toBeDefined();
    expect(screen.queryByText("Freshness")).toBeNull();
  });

  it("renders linked active rows with freshness and available bounded action copy", () => {
    render(
      <DeploymentTable
        deployments={[baseDeployment]}
        selectedDeploymentId={null}
        onSelectDeployment={vi.fn()}
      />,
    );

    expect(screen.getByText("Active")).toBeDefined();
    expect(screen.getByText("Connected")).toBeDefined();
    expect(screen.getByText("Linked")).toBeDefined();
    expect(
      screen.getByText("Hosted posture reflects an active deployment link with current metadata visibility."),
    ).toBeDefined();
    expect(screen.getByText("Rotation available")).toBeDefined();
  });

  it("renders pending enrollment rows as unavailable without a freshness badge", () => {
    render(
      <DeploymentTable
        deployments={[
          makeDeployment({
            id: "dep-pending",
            display_name: "Pending Gateway",
            enrollment_state: "pending",
            freshness_status: null,
            last_seen_at: null,
          }),
        ]}
        selectedDeploymentId={null}
        onSelectDeployment={vi.fn()}
      />,
    );

    expect(screen.getAllByText("Pending enrollment").length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getByText(
        "Hosted visibility remains pending enrollment until the deployment finishes linking.",
      ),
    ).toBeDefined();
    expect(screen.getByText("Rotation unavailable")).toBeDefined();
    expect(screen.queryByText("Connected")).toBeNull();
  });

  it("renders revoked and unlinked records as unavailable states", () => {
    render(
      <DeploymentTable
        deployments={[
          makeDeployment({
            id: "dep-revoked",
            display_name: "Revoked Gateway",
            enrollment_state: "revoked",
            freshness_status: null,
            revoked_at: "2026-03-22T10:00:00Z",
          }),
          makeDeployment({
            id: "dep-unlinked",
            display_name: "Unlinked Gateway",
            enrollment_state: "unlinked",
            freshness_status: null,
            unlinked_at: "2026-03-22T10:00:00Z",
          }),
        ]}
        selectedDeploymentId={null}
        onSelectDeployment={vi.fn()}
      />,
    );

    expect(screen.getAllByText("Revoked").length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getByText("Hosted visibility is retained for audit context, but this link has been revoked."),
    ).toBeDefined();
    expect(screen.getAllByText("Rotation unavailable").length).toBeGreaterThanOrEqual(2);

    expect(screen.getAllByText("Unlinked").length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getByText(
        "Hosted visibility is descriptive only because this deployment is no longer linked.",
      ),
    ).toBeDefined();
  });

  it("renders stale and offline visibility rows as blocked bounded-action states", () => {
    render(
      <DeploymentTable
        deployments={[
          makeDeployment({
            id: "dep-stale",
            display_name: "Stale Gateway",
            freshness_status: "stale",
            freshness_reason: "Last heartbeat 20 minutes ago",
          }),
          makeDeployment({
            id: "dep-offline",
            display_name: "Offline Gateway",
            freshness_status: "offline",
            freshness_reason: "No heartbeat for 2 hours",
          }),
        ]}
        selectedDeploymentId={null}
        onSelectDeployment={vi.fn()}
      />,
    );

    expect(screen.getByText("Stale visibility")).toBeDefined();
    expect(screen.getByText("Offline visibility")).toBeDefined();
    expect(screen.getByText("Stale")).toBeDefined();
    expect(screen.getByText("Offline")).toBeDefined();
    expect(screen.getAllByText("Rotation blocked").length).toBe(2);
  });

  it("preserves row click selection behavior", () => {
    const onSelectDeployment = vi.fn();

    render(
      <DeploymentTable
        deployments={[baseDeployment]}
        selectedDeploymentId={null}
        onSelectDeployment={onSelectDeployment}
      />,
    );

    fireEvent.click(screen.getByText("Production Gateway"));

    expect(onSelectDeployment).toHaveBeenCalledTimes(1);
    expect(onSelectDeployment).toHaveBeenCalledWith(baseDeployment);
  });

  it("renders empty state when no deployments are present", () => {
    render(
      <DeploymentTable
        deployments={[]}
        selectedDeploymentId={null}
        onSelectDeployment={vi.fn()}
      />,
    );

    expect(screen.getByText("No deployments linked")).toBeDefined();
  });
});
