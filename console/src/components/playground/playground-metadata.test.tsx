import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PlaygroundMetadata } from "@/components/playground/playground-metadata";
import { renderWithProviders } from "@/test/render";

describe("playground-metadata", () => {
  it("renders the immediate routing, tenant, and policy evidence", () => {
    renderWithProviders(
      <PlaygroundMetadata
        requestId="req-play-001"
        tenantId="tenant-alpha"
        routeTarget="premium"
        routeReason="complex_prompt"
        provider="openai-compatible"
        cacheHit={false}
        fallbackUsed
        latencyMs={187}
        policyMode="auto"
        policyOutcome="allowed"
      />,
    );

    expect(screen.getByText("Route target")).toBeInTheDocument();
    expect(screen.getByText("Route reason")).toBeInTheDocument();
    expect(screen.getByText("Tenant")).toBeInTheDocument();
    expect(screen.getByText("Provider")).toBeInTheDocument();
    expect(screen.getByText("Policy mode")).toBeInTheDocument();
    expect(screen.getByText("Policy outcome")).toBeInTheDocument();
    expect(screen.getByText("Cache hit")).toBeInTheDocument();
    expect(screen.getByText("Fallback used")).toBeInTheDocument();
    expect(screen.getByText("Latency")).toBeInTheDocument();
    expect(screen.getByText("tenant-alpha")).toBeInTheDocument();
    expect(screen.getByText("complex_prompt")).toBeInTheDocument();
    expect(screen.getByText("auto")).toBeInTheDocument();
    expect(screen.getByText("No")).toBeInTheDocument();
    expect(screen.getByText("Yes")).toBeInTheDocument();
    expect(screen.getByText("187 ms")).toBeInTheDocument();
  });
});
