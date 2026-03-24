import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import TrustBoundaryPage from "@/app/trust-boundary/page";

describe("TrustBoundaryPage", () => {
  it("renders the page heading", () => {
    render(<TrustBoundaryPage />);
    expect(
      screen.getByRole("heading", { name: "Hosted trust boundary" })
    ).toBeInTheDocument();
  });

  it("renders shared canonical intro language", () => {
    render(<TrustBoundaryPage />);
    expect(
      screen.getAllByText(
        "Hosted onboarding establishes deployment identity and operator visibility without moving request-serving or policy authority into the hosted plane."
      ).length
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "Hosted fleet posture describes what deployments most recently reported, not what the local runtime is enforcing right now."
      ).length
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(
        "If the hosted control plane is unreachable, Nebula keeps serving with local policy and local provider access. Hosted freshness simply ages toward stale or offline until heartbeats resume."
      ).length
    ).toBeGreaterThan(0);
  });

  it("renders Metadata-only by default", () => {
    render(<TrustBoundaryPage />);
    expect(screen.getByText("Metadata-only by default")).toBeInTheDocument();
  });

  it("renders Excluded by default section", () => {
    render(<TrustBoundaryPage />);
    expect(screen.getByText("Excluded by default")).toBeInTheDocument();
  });

  it("renders all freshness state keys", () => {
    render(<TrustBoundaryPage />);
    expect(screen.getByText("connected")).toBeInTheDocument();
    expect(screen.getByText("degraded")).toBeInTheDocument();
    expect(screen.getByText("stale")).toBeInTheDocument();
    expect(screen.getByText("offline")).toBeInTheDocument();
  });

  it("renders the freshness warning and not-in-path statements", () => {
    render(<TrustBoundaryPage />);
    expect(
      screen.getByText("Hosted freshness is not local runtime authority.")
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Nebula's hosted control plane is not in the request-serving path."
      )
    ).toBeInTheDocument();
  });

  it("renders hosted fleet posture guidance and prohibited authority guardrails", () => {
    render(<TrustBoundaryPage />);
    expect(
      screen.getByRole("heading", { name: "Hosted fleet posture guidance" })
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(
        "Use freshness and dependency summaries to prioritize investigation, then confirm serving-time behavior from the local runtime and its observability surfaces."
      ).length
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByRole("heading", { name: "Reinforcement guardrails" }).length
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(
        "Do not say the hosted plane serves traffic or sits in the request-serving path."
      )
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Do not say the hosted plane has local runtime authority."
      )
    ).toBeInTheDocument();
  });

  it("renders the pilot onboarding, outage, and remote-management sections", () => {
    render(<TrustBoundaryPage />);
    expect(
      screen.getByRole("heading", { name: "Pilot onboarding flow" })
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Create a deployment slot in the hosted plane, exchange a short-lived enrollment token from the self-hosted gateway, then continue with a deployment-scoped hosted-link credential."
      )
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Hosted outage behavior" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Remote-management safety limits" })
    ).toBeInTheDocument();
    expect(
      screen.getByText(/v2.0 allows one audited rotate_deployment_credential action only\./)
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(
        "Deployment-bound hosted actions are limited to audited credential rotation and related status visibility; they never imply tenant-policy, routing, fallback, or provider-credential authority."
      ).length
    ).toBeGreaterThan(0);
  });

  it("indicates the page is public", () => {
    render(<TrustBoundaryPage />);
    expect(
      screen.getByText(/public and accessible before authentication/)
    ).toBeInTheDocument();
  });
});
