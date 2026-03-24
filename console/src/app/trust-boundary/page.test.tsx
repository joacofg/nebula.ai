import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import TrustBoundaryPage from "@/app/trust-boundary/page";
import { getHostedContractContent } from "@/lib/hosted-contract";

describe("TrustBoundaryPage", () => {
  const { copy, reinforcement } = getHostedContractContent();

  it("renders the page heading", () => {
    render(<TrustBoundaryPage />);
    expect(
      screen.getByRole("heading", { name: "Hosted trust boundary" })
    ).toBeInTheDocument();
  });

  it("renders shared canonical intro language", () => {
    render(<TrustBoundaryPage />);
    expect(screen.getAllByText(reinforcement.allowedDescriptiveClaims[3]).length).toBeGreaterThan(0);
    expect(screen.getAllByText(reinforcement.allowedDescriptiveClaims[1]).length).toBeGreaterThan(0);
    expect(screen.getAllByText(copy.outageBody).length).toBeGreaterThan(0);
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
    expect(screen.getByText(copy.freshnessWarning)).toBeInTheDocument();
    expect(screen.getByText(copy.notInPath)).toBeInTheDocument();
  });

  it("renders hosted fleet posture guidance and prohibited authority guardrails", () => {
    render(<TrustBoundaryPage />);
    expect(
      screen.getByRole("heading", { name: "Hosted fleet posture guidance" })
    ).toBeInTheDocument();
    expect(screen.getAllByText(reinforcement.operatorReadingGuidance[1]).length).toBeGreaterThan(0);
    expect(
      screen.getAllByRole("heading", { name: "Reinforcement guardrails" }).length
    ).toBeGreaterThan(0);
    expect(screen.getByText(reinforcement.prohibitedAuthorityClaims[0])).toBeInTheDocument();
    expect(screen.getByText(reinforcement.prohibitedAuthorityClaims[1])).toBeInTheDocument();
  });

  it("renders the pilot onboarding, outage, and remote-management sections", () => {
    render(<TrustBoundaryPage />);
    expect(
      screen.getByRole("heading", { name: copy.onboardingHeading })
    ).toBeInTheDocument();
    expect(screen.getByText(copy.onboardingBody)).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: copy.outageHeading })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: copy.remoteLimitsHeading })
    ).toBeInTheDocument();
    expect(screen.getByText(copy.remoteLimitsBody)).toBeInTheDocument();
    expect(screen.getAllByText(reinforcement.boundedActionPhrasing.description).length).toBeGreaterThan(0);
  });

  it("renders the public trust walkthrough in canonical proof order", () => {
    render(<TrustBoundaryPage />);

    const introClaim = screen.getAllByText(reinforcement.allowedDescriptiveClaims[3])[0];
    const fleetClaim = screen.getAllByText(reinforcement.allowedDescriptiveClaims[1])[0];
    const cardHeading = screen.getByText(copy.heading);
    const onboardingHeading = screen.getByRole("heading", { name: copy.onboardingHeading });
    const guidanceHeading = screen.getByRole("heading", { name: "Hosted fleet posture guidance" });
    const remoteLimitsHeading = screen.getByRole("heading", { name: copy.remoteLimitsHeading });

    expect(introClaim.compareDocumentPosition(cardHeading)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
    expect(fleetClaim.compareDocumentPosition(cardHeading)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
    expect(cardHeading.compareDocumentPosition(onboardingHeading)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
    expect(onboardingHeading.compareDocumentPosition(guidanceHeading)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
    expect(guidanceHeading.compareDocumentPosition(remoteLimitsHeading)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
  });

  it("indicates the page is public", () => {
    render(<TrustBoundaryPage />);
    expect(
      screen.getByText(/public and accessible before authentication/)
    ).toBeInTheDocument();
  });
});
