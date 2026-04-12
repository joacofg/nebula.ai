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

  it("renders retention lifecycle runtime metrics without introducing a dedicated dashboard", () => {
    renderWithProviders(
      <RuntimeHealthCards
        isLoading={false}
        dependencies={{
          retention_lifecycle: {
            status: "degraded",
            required: false,
            detail: "Retention lifecycle cleanup failed on its last attempt.",
            last_status: "failed",
            last_run_at: "2026-04-12T01:02:03Z",
            last_attempted_run_at: "2026-04-12T01:05:00Z",
            last_deleted_count: 4,
            last_eligible_count: 4,
            last_error: "cleanup query timed out",
          },
        }}
      />,
    );

    expect(screen.getByText("retention_lifecycle")).toBeInTheDocument();
    expect(screen.getByText("Last status")).toBeInTheDocument();
    expect(screen.getByText("failed")).toBeInTheDocument();
    expect(screen.getByText("Deleted rows")).toBeInTheDocument();
    expect(screen.getAllByText("4")).toHaveLength(2);
    expect(screen.getByText("Last error")).toBeInTheDocument();
    expect(screen.getByText("cleanup query timed out")).toBeInTheDocument();
    expect(screen.queryByText(/retention dashboard/i)).not.toBeInTheDocument();
  });
});
