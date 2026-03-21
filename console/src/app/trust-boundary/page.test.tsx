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

  it("indicates the page is public", () => {
    render(<TrustBoundaryPage />);
    expect(
      screen.getByText(/public and accessible before authentication/)
    ).toBeInTheDocument();
  });
});
