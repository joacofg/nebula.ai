import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ObservabilityPage from "@/app/(console)/observability/page";
import { renderWithProviders } from "@/test/render";

const adminApi = vi.hoisted(() => ({
  listTenants: vi.fn(),
  listUsageLedger: vi.fn(),
}));

vi.mock("@/lib/admin-api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/admin-api")>("@/lib/admin-api");
  return {
    ...actual,
    listTenants: adminApi.listTenants,
    listUsageLedger: adminApi.listUsageLedger,
  };
});

describe("observability-page", () => {
  it("frames observability as persisted request evidence plus dependency-health context", async () => {
    adminApi.listTenants.mockResolvedValue([
      {
        id: "default",
        name: "Default Workspace",
        description: "Bootstrap tenant",
        metadata: {},
        active: true,
        created_at: "2026-03-16T12:00:00Z",
        updated_at: "2026-03-16T12:00:00Z",
      },
    ]);
    adminApi.listUsageLedger.mockResolvedValue([
      {
        request_id: "req-123",
        tenant_id: "default",
        requested_model: "nebula-auto",
        final_route_target: "premium",
        final_provider: "openai-compatible",
        fallback_used: false,
        cache_hit: false,
        response_model: "openai/gpt-4o-mini",
        prompt_tokens: 12,
        completion_tokens: 6,
        total_tokens: 18,
        estimated_cost: 0.012,
        latency_ms: 120,
        timestamp: "2026-03-16T22:00:00Z",
        terminal_status: "completed",
        route_reason: "direct_premium_model",
        policy_outcome: "allowed",
      },
    ]);

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          dependencies: {
            postgres: { status: "healthy", required: true, detail: "reachable" },
          },
        }),
      }),
    );

    renderWithProviders(<ObservabilityPage />, { adminKey: "nebula-admin-key" });

    expect(await screen.findByRole("heading", { name: "Persisted request evidence" })).toBeInTheDocument();
    expect(
      screen.getByText(/Inspect the persisted usage ledger for recorded request outcomes/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/then use dependency health as supporting runtime context/i),
    ).toBeInTheDocument();
    expect(screen.queryByText(/replace the public request/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/workspace/i)).not.toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Dependency health context" })).toBeInTheDocument();
    expect(
      screen.getByText(/These dependency states do not replace the ledger record; they provide supporting runtime context/i),
    ).toBeInTheDocument();

    vi.unstubAllGlobals();
  });
});
