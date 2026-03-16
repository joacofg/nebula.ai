import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RuntimeHealthCards } from "@/components/health/runtime-health-cards";
import { renderWithProviders } from "@/test/render";

describe("runtime-health-cards", () => {
  it("renders ready, degraded, and not_ready cards with explicit text", () => {
    renderWithProviders(
      <RuntimeHealthCards
        isLoading={false}
        dependencies={{
          gateway: {
            status: "ready",
            required: true,
            detail: "FastAPI application is running.",
          },
          semantic_cache: {
            status: "degraded",
            required: false,
            detail: "Qdrant unavailable.",
          },
          premium_provider: {
            status: "not_ready",
            required: false,
            detail: "Premium provider offline.",
          },
        }}
      />,
    );

    expect(screen.getByText("gateway")).toBeInTheDocument();
    expect(screen.getByText("ready")).toBeInTheDocument();
    expect(screen.getByText("degraded")).toBeInTheDocument();
    expect(screen.getByText("not_ready")).toBeInTheDocument();
    expect(screen.getByText("premium_provider")).toBeInTheDocument();
    expect(
      screen.getByText("Optional dependency degradation does not block gateway readiness."),
    ).toBeInTheDocument();
  });
});
