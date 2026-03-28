import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ObservabilityPage from "@/app/(console)/observability/page";
import { renderWithProviders } from "@/test/render";

const adminApi = vi.hoisted(() => ({
  listTenants: vi.fn(),
  listUsageLedger: vi.fn(),
  getTenantRecommendations: vi.fn(),
}));

vi.mock("@/lib/admin-api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/admin-api")>("@/lib/admin-api");
  return {
    ...actual,
    listTenants: adminApi.listTenants,
    listUsageLedger: adminApi.listUsageLedger,
    getTenantRecommendations: adminApi.getTenantRecommendations,
  };
});

describe("observability-page", () => {
  it("frames observability as persisted request evidence plus grounded recommendation and dependency context", async () => {
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
        route_signals: null,
      },
    ]);
    adminApi.getTenantRecommendations.mockResolvedValue({
      tenant_id: "default",
      generated_at: "2026-03-27T18:00:00Z",
      window_requests_evaluated: 24,
      recommendations: [
        {
          code: "cache-tighten-threshold",
          title: "Tighten cache similarity threshold",
          priority: 1,
          category: "cache",
          summary: "Recent ledger-backed traffic shows reuse with mixed downstream outcomes.",
          recommended_action: "Raise the similarity threshold in policy preview before saving.",
          evidence: [
            { label: "Requests evaluated", value: "24" },
            { label: "Estimated hit rate", value: "42%" },
          ],
        },
      ],
      cache_summary: {
        enabled: true,
        similarity_threshold: 0.82,
        max_entry_age_hours: 48,
        runtime_status: "degraded",
        runtime_detail: "Qdrant latency is elevated but cache lookups still succeed.",
        estimated_hit_rate: 0.42,
        avoided_premium_cost_usd: 1.275,
        insights: [
          {
            code: "cache-health-watch",
            title: "Watch degraded cache runtime",
            level: "notice",
            summary: "Recent cache reuse remains valuable, but degraded runtime may reduce consistency.",
            evidence: [{ label: "Runtime status", value: "degraded" }],
          },
        ],
      },
    });

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
      screen.getByText(/use dependency health and recommendation summaries as supporting runtime context/i),
    ).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Next-best actions from recent tenant traffic" })).toBeInTheDocument();
    expect(
      screen.getByText(/Recommendations are derived from recent ledger-backed traffic plus supporting runtime context/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/not black-box optimization/i)).toBeInTheDocument();
    expect(await screen.findByText("Tighten cache similarity threshold")).toBeInTheDocument();
    expect(screen.getByText(/Raise the similarity threshold in policy preview before saving/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Cache effectiveness and runtime controls" })).toBeInTheDocument();
    expect(screen.getByText("Similarity threshold")).toBeInTheDocument();
    expect(screen.getByText("0.82")).toBeInTheDocument();
    expect(screen.getByText("Max entry age")).toBeInTheDocument();
    expect(screen.getByText("48 hours")).toBeInTheDocument();
    expect(screen.getByText(/Tune these controls in the existing policy editor; this page stays inspection-only/i)).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Dependency health context" })).toBeInTheDocument();
    expect(
      screen.getByText(/These dependency states do not replace the ledger record; they provide supporting runtime context/i),
    ).toBeInTheDocument();

    vi.unstubAllGlobals();
  });
});
