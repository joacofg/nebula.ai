import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TrustBoundaryCard } from "@/components/hosted/trust-boundary-card";

describe("TrustBoundaryCard", () => {
  it("renders the heading and metadata-only label", () => {
    render(<TrustBoundaryCard />);

    expect(
      screen.getByText("What this deployment shares")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Metadata-only by default")
    ).toBeInTheDocument();
  });

  it("renders the not-in-path statement", () => {
    render(<TrustBoundaryCard />);

    expect(
      screen.getByText(
        "Nebula's hosted control plane is not in the request-serving path."
      )
    ).toBeInTheDocument();
  });

  it("renders the freshness warning", () => {
    render(<TrustBoundaryCard />);

    expect(
      screen.getByText(
        "Hosted freshness is not local runtime authority."
      )
    ).toBeInTheDocument();
  });

  it("renders the footnote", () => {
    render(<TrustBoundaryCard />);

    expect(
      screen.getByText(
        "Richer diagnostics must be operator-initiated exceptions to this default contract."
      )
    ).toBeInTheDocument();
  });

  it("renders all 12 exported field labels", () => {
    render(<TrustBoundaryCard />);

    const expectedLabels = [
      "Deployment identity",
      "Deployment display name",
      "Environment",
      "Operator-assigned labels",
      "Nebula version",
      "Capability flags",
      "Registration timestamp",
      "Last-seen timestamp",
      "Hosted freshness status",
      "Hosted freshness reason",
      "Coarse dependency summary",
      "Remote-action audit summary",
    ];

    for (const label of expectedLabels) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it("renders the excluded-by-default heading and all 6 items", () => {
    render(<TrustBoundaryCard />);

    expect(screen.getByText("Excluded by default")).toBeInTheDocument();

    const excluded = [
      "Raw prompts",
      "Raw responses",
      "Provider credentials",
      "Raw usage-ledger rows",
      "Tenant secrets",
      "Authoritative runtime policy state",
    ];

    for (const item of excluded) {
      expect(screen.getByText(item)).toBeInTheDocument();
    }
  });

  it("renders the freshness state keys", () => {
    render(<TrustBoundaryCard />);

    expect(screen.getByText("connected")).toBeInTheDocument();
    expect(screen.getByText("degraded")).toBeInTheDocument();
    expect(screen.getByText("stale")).toBeInTheDocument();
    expect(screen.getByText("offline")).toBeInTheDocument();
  });
});
