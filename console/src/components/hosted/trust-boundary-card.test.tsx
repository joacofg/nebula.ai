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

  it("renders shared operator guidance and reinforcement guardrails", () => {
    render(<TrustBoundaryCard />);

    expect(
      screen.getByRole("heading", { name: "Shared reading guidance" })
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Read hosted fleet posture as an operator summary derived from deployment metadata exports."
      )
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Reinforcement guardrails" })
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Hosted summaries are metadata-backed and descriptive only."
      )
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Hosted fleet posture describes what deployments most recently reported, not what the local runtime is enforcing right now."
      )
    ).toBeInTheDocument();
  });

  it("renders bounded action phrasing from the shared contract", () => {
    render(<TrustBoundaryCard />);

    expect(
      screen.getByText("Audited credential rotation only")
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Deployment-bound hosted actions are limited to audited credential rotation and related status visibility; they never imply tenant-policy, routing, fallback, or provider-credential authority."
      )
    ).toBeInTheDocument();
  });

  it("renders the hosted evidence vocabulary without implying raw export or runtime authority", () => {
    render(<TrustBoundaryCard />);

    expect(screen.getByText("Retained request detail stays local to the persisted ledger row while that governed row still exists.")).toBeInTheDocument();
    expect(screen.getByText("Suppressed means governance removed or never wrote specific metadata fields, so those fields are no longer available from the ledger later.")).toBeInTheDocument();
    expect(screen.getByText("Deleted means governed retention removed the entire row at expiration; Nebula should not imply recovery, soft-delete archives, or hidden raw exports afterward.")).toBeInTheDocument();
    expect(screen.getByText("Not hosted means the hosted control plane does not receive raw usage-ledger rows and cannot replace the local row as request-level evidence.")).toBeInTheDocument();
    expect(screen.getByText("Raw usage-ledger rows")).toBeInTheDocument();
    expect(screen.getByText("Authoritative runtime policy state")).toBeInTheDocument();
  });

  it("renders the freshness warning", () => {
    render(<TrustBoundaryCard />);

    expect(
      screen.getByText("Hosted freshness is not local runtime authority.")
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
