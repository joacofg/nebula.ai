import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { FleetPostureSummary } from "@/components/deployments/fleet-posture-summary";
import type { DeploymentRecord } from "@/lib/admin-api";
import { getHostedContractContent } from "@/lib/hosted-contract";

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

describe("FleetPostureSummary", () => {
  const { reinforcement } = getHostedContractContent();

  it("renders meaningful mixed-fleet posture counts with hosted trust-boundary copy", () => {
    const deployments: DeploymentRecord[] = [
      baseDeployment,
      { ...baseDeployment, id: "dep-2", display_name: "Secondary Gateway" },
      {
        ...baseDeployment,
        id: "dep-3",
        display_name: "Pending Gateway",
        enrollment_state: "pending",
        freshness_status: null,
      },
      {
        ...baseDeployment,
        id: "dep-4",
        display_name: "Stale Gateway",
        freshness_status: "stale",
      },
      {
        ...baseDeployment,
        id: "dep-5",
        display_name: "Offline Gateway",
        freshness_status: "offline",
      },
      {
        ...baseDeployment,
        id: "dep-6",
        display_name: "Unsupported Gateway",
        capability_flags: [],
      },
    ];

    render(<FleetPostureSummary deployments={deployments} />);

    expect(screen.getByRole("heading", { name: "Metadata-backed hosted fleet posture" })).toBeInTheDocument();
    expect(screen.getByText("6 deployments")).toBeInTheDocument();
    expect(screen.getByText("Linked and current")).toBeInTheDocument();
    expect(screen.getByText("Pending enrollment")).toBeInTheDocument();
    expect(screen.getByText("Stale or offline visibility")).toBeInTheDocument();
    expect(screen.getByText("Bounded actions blocked")).toBeInTheDocument();
    expect(screen.getByText(reinforcement.allowedDescriptiveClaims[0])).toBeInTheDocument();
    expect(screen.getByText(reinforcement.operatorReadingGuidance[1])).toBeInTheDocument();
    expect(screen.getByText(reinforcement.boundedActionPhrasing.description)).toBeInTheDocument();

    const counts = screen.getAllByText(/^[0-9]+$/).map((node) => node.textContent);
    expect(counts).toEqual(["3", "1", "2", "4"]);
  });

  it("renders a coherent empty-state summary without implying hosted authority", () => {
    render(<FleetPostureSummary deployments={[]} />);

    expect(screen.getByText("0 deployments")).toBeInTheDocument();
    expect(
      screen.getByText("Create a deployment slot to start enrollment and populate hosted fleet posture."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("No deployments currently report linked, current metadata visibility."),
    ).toBeInTheDocument();
    expect(screen.getByText("No deployments are waiting to finish enrollment.")).toBeInTheDocument();
    expect(
      screen.getByText("All linked deployments are reporting current metadata visibility."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Every linked deployment currently allows the bounded hosted action scope."),
    ).toBeInTheDocument();
    expect(screen.queryByText(/authoritative health/i)).not.toBeInTheDocument();
  });

  it("keeps all-pending fleets readable and descriptive", () => {
    render(
      <FleetPostureSummary
        deployments={[
          {
            ...baseDeployment,
            id: "dep-pending-1",
            display_name: "Pending One",
            enrollment_state: "pending",
            freshness_status: null,
          },
          {
            ...baseDeployment,
            id: "dep-pending-2",
            display_name: "Pending Two",
            enrollment_state: "pending",
            freshness_status: null,
          },
        ]}
      />,
    );

    const counts = screen.getAllByText(/^[0-9]+$/).map((node) => node.textContent);
    expect(counts).toEqual(["0", "2", "0", "2"]);
    expect(
      screen.getByText("Enrollment is still pending, so hosted visibility remains descriptive and incomplete."),
    ).toBeInTheDocument();
    expect(
      screen.getByText(reinforcement.allowedDescriptiveClaims[1]),
    ).toBeInTheDocument();
  });
});
