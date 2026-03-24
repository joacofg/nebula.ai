import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ObservabilityPage from "./page";

const listTenants = vi.fn();
const listUsageLedger = vi.fn();

vi.mock("@/lib/admin-api", () => ({
  listTenants: (...args: unknown[]) => listTenants(...args),
  listUsageLedger: (...args: unknown[]) => listUsageLedger(...args),
}));

vi.mock("@/lib/admin-session-provider", () => ({
  useAdminSession: () => ({ adminKey: "nebula-admin-key" }),
}));

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ObservabilityPage />
    </QueryClientProvider>,
  );
}

describe("ObservabilityPage", () => {
  beforeEach(() => {
    listTenants.mockResolvedValue([{ id: "tenant-alpha", name: "Tenant Alpha" }]);
    listUsageLedger.mockResolvedValue([
      {
        request_id: "req-integrated-001",
        tenant_id: "tenant-alpha",
        requested_model: "gpt-4o-mini",
        final_route_target: "premium",
        final_provider: "openai-compatible",
        fallback_used: false,
        cache_hit: false,
        response_model: "gpt-4o-mini",
        prompt_tokens: 12,
        completion_tokens: 18,
        total_tokens: 30,
        estimated_cost: 0.0042,
        latency_ms: 210,
        timestamp: "2026-03-23T18:00:00Z",
        terminal_status: "completed",
        route_reason: "complexity_high",
        policy_outcome: "allowed",
      },
    ]);

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          dependencies: {
            postgres: { status: "healthy", required: true, detail: "ready" },
            qdrant: { status: "degraded", required: false, detail: "warming" },
          },
        }),
      }),
    );
  });

  it("renders the integrated observability framing and dependency health context", async () => {
    renderPage();

    expect(await screen.findByText("Persisted request explanation")).toBeInTheDocument();
    expect(
      screen.getByText(/public X-Request-ID and X-Nebula-\* headers/i),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Dependency health" })).toBeInTheDocument();
    expect(
      screen.getByText(/Required dependency failures block confidence immediately/i),
    ).toBeInTheDocument();
    expect(await screen.findAllByText("tenant-alpha")).toHaveLength(2);
    expect(await screen.findAllByText("Route target")).toHaveLength(3);
  });
});
