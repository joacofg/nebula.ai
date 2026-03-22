import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { DeploymentTable } from "./deployment-table";
import type { DeploymentRecord } from "@/lib/admin-api";

const mockDeployment: DeploymentRecord = {
  id: "dep-1",
  display_name: "Production Gateway",
  environment: "production",
  enrollment_state: "active",
  nebula_version: "1.2.0",
  capability_flags: ["semantic_cache"],
  enrolled_at: "2026-03-20T00:00:00Z",
  revoked_at: null,
  unlinked_at: null,
  created_at: "2026-03-19T00:00:00Z",
  updated_at: "2026-03-20T00:00:00Z",
  last_seen_at: "2026-03-22T12:00:00Z",
  freshness_status: "connected",
  freshness_reason: "Last heartbeat 3 minutes ago",
  dependency_summary: { healthy: ["gateway"], degraded: [], unavailable: [] },
};

describe("DeploymentTable", () => {
  it("renders Freshness column header", () => {
    render(
      <DeploymentTable
        deployments={[mockDeployment]}
        selectedDeploymentId={null}
        onSelectDeployment={vi.fn()}
      />,
    );
    expect(screen.getByText("Freshness")).toBeDefined();
  });

  it("renders Version column header", () => {
    render(
      <DeploymentTable
        deployments={[mockDeployment]}
        selectedDeploymentId={null}
        onSelectDeployment={vi.fn()}
      />,
    );
    expect(screen.getByText("Version")).toBeDefined();
  });

  it("renders Last Seen column header", () => {
    render(
      <DeploymentTable
        deployments={[mockDeployment]}
        selectedDeploymentId={null}
        onSelectDeployment={vi.fn()}
      />,
    );
    expect(screen.getByText("Last Seen")).toBeDefined();
  });

  it("does not render Status or Enrolled column headers", () => {
    render(
      <DeploymentTable
        deployments={[mockDeployment]}
        selectedDeploymentId={null}
        onSelectDeployment={vi.fn()}
      />,
    );
    expect(screen.queryByText("Status")).toBeNull();
    expect(screen.queryByText("Enrolled")).toBeNull();
  });

  it("renders Connected freshness badge for connected deployment", () => {
    render(
      <DeploymentTable
        deployments={[mockDeployment]}
        selectedDeploymentId={null}
        onSelectDeployment={vi.fn()}
      />,
    );
    expect(screen.getByText("Connected")).toBeDefined();
  });

  it("renders version string in table", () => {
    render(
      <DeploymentTable
        deployments={[mockDeployment]}
        selectedDeploymentId={null}
        onSelectDeployment={vi.fn()}
      />,
    );
    expect(screen.getByText("1.2.0")).toBeDefined();
  });

  it("renders empty state when no deployments", () => {
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
