import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PlaygroundMetadata } from "@/components/playground/playground-metadata";
import { renderWithProviders } from "@/test/render";

describe("playground-metadata", () => {
  it("renders the immediate metadata labels and explicit yes-no values", () => {
    renderWithProviders(
      <PlaygroundMetadata
        requestId="req-play-001"
        routeTarget="premium"
        provider="openai-compatible"
        cacheHit={false}
        fallbackUsed
        latencyMs={187}
        policyOutcome="allowed"
      />,
    );

    expect(screen.getByText("Route target")).toBeInTheDocument();
    expect(screen.getByText("Provider")).toBeInTheDocument();
    expect(screen.getByText("Cache hit")).toBeInTheDocument();
    expect(screen.getByText("Fallback")).toBeInTheDocument();
    expect(screen.getByText("Latency")).toBeInTheDocument();
    expect(screen.getByText("Policy outcome")).toBeInTheDocument();
    expect(screen.getByText("No")).toBeInTheDocument();
    expect(screen.getByText("Yes")).toBeInTheDocument();
    expect(screen.getByText("187 ms")).toBeInTheDocument();
  });
});
