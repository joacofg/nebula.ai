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
    expect(screen.getByText("not ready")).toBeInTheDocument();
    expect(screen.getByText("premium_provider")).toBeInTheDocument();
    expect(
      screen.getByText("Optional dependency degradation does not block gateway readiness."),
    ).toBeInTheDocument();
  });

  it("renders resilience metadata for critical, optional, and recovering dependencies", () => {
    renderWithProviders(
      <RuntimeHealthCards
        isLoading={false}
        dependencies={{
          governance_store: {
            status: "not_ready",
            required: true,
            detail: "Governance queries failed.",
            dependency_class: "serving_critical",
            lifecycle_state: "not_ready",
            serving_effect: "fail_closed",
            reason_code: "governance_query_failed",
            recovering: false,
            enabled: true,
            last_failure_at: "2026-04-12T01:00:00Z",
          },
          semantic_cache: {
            status: "degraded",
            required: false,
            detail: "Semantic cache unavailable; requests continue without cache hits.",
            dependency_class: "serving_optional",
            lifecycle_state: "degraded",
            serving_effect: "continuity_limited",
            reason_code: "semantic_cache_unavailable",
            recovering: false,
            enabled: true,
          },
          premium_provider: {
            status: "recovering",
            required: false,
            detail: "Premium provider connectivity restored; recovery checks are still running.",
            dependency_class: "serving_optional",
            lifecycle_state: "recovering",
            serving_effect: "continuity_limited",
            reason_code: "premium_provider_recovered",
            recovering: true,
            last_failure_at: "2026-04-12T00:55:00Z",
            last_recovery_at: "2026-04-12T01:03:00Z",
          },
        }}
      />,
    );

    expect(screen.getAllByText("Dependency class")).toHaveLength(3);
    expect(screen.getByText("serving critical")).toBeInTheDocument();
    expect(screen.getAllByText("serving optional")).toHaveLength(2);
    expect(screen.getAllByText("Lifecycle state")).toHaveLength(3);
    expect(screen.getAllByText("recovering")).toHaveLength(2);
    expect(screen.getAllByText("Serving effect")).toHaveLength(3);
    expect(screen.getByText("fail closed")).toBeInTheDocument();
    expect(screen.getAllByText("continuity limited")).toHaveLength(2);
    expect(screen.getAllByText("Reason code")).toHaveLength(3);
    expect(screen.getByText("governance query failed")).toBeInTheDocument();
    expect(screen.getByText("semantic cache unavailable")).toBeInTheDocument();
    expect(screen.getByText("premium provider recovered")).toBeInTheDocument();
    expect(screen.getAllByText("Enabled")).toHaveLength(2);
    expect(screen.getAllByText("Yes")).toHaveLength(3);
    expect(screen.getAllByText("Recovering")).toHaveLength(3);
    expect(screen.getAllByText("No")).toHaveLength(2);
    expect(screen.getAllByText("Last failure")).toHaveLength(2);
    expect(screen.getByText("2026-04-12T01:00:00Z")).toBeInTheDocument();
    expect(screen.getAllByText("Last recovery")).toHaveLength(1);
    expect(screen.getByText("2026-04-12T01:03:00Z")).toBeInTheDocument();
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
