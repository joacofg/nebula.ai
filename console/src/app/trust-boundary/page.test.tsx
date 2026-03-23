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

  it("renders the recommended-for-pilots intro", () => {
    render(<TrustBoundaryPage />);
    expect(
      screen.getByText(/recommended for pilots/)
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Hosted-control-plane outages degrade visibility only; they do not break the self-hosted serving path."
      )
    ).toBeInTheDocument();
  });

  it("renders Metadata-only by default", () => {
    render(<TrustBoundaryPage />);
    expect(
      screen.getByText("Metadata-only by default")
    ).toBeInTheDocument();
  });

  it("renders Excluded by default section", () => {
    render(<TrustBoundaryPage />);
    expect(
      screen.getByText("Excluded by default")
    ).toBeInTheDocument();
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
  });

  it("indicates the page is public", () => {
    render(<TrustBoundaryPage />);
    expect(
      screen.getByText(/public and accessible before authentication/)
    ).toBeInTheDocument();
  });
});
