import { screen, within } from "@testing-library/react";
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
  it("frames observability around selected request evidence with bounded supporting context", async () => {
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
      calibration_summary: {
        tenant_id: "default",
        scope: "tenant",
        state: "sufficient",
        state_reason: "Recent eligible calibrated rows meet the tenant sufficiency threshold.",
        generated_at: "2026-03-27T18:00:00Z",
        latest_eligible_request_at: "2026-03-27T17:15:00Z",
        latest_any_request_at: "2026-03-27T17:15:00Z",
        eligible_request_count: 12,
        sufficient_request_count: 12,
        thin_request_threshold: 5,
        staleness_threshold_hours: 24,
        excluded_request_count: 1,
        gated_request_count: 0,
        degraded_request_count: 1,
        excluded_reasons: [{ reason: "policy_forced_route", count: 1 }],
        gated_reasons: [],
        degraded_reasons: [{ reason: "missing_route_signals", count: 1 }],
      },
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

    expect(await screen.findByRole("heading", { name: "Selected request evidence first" })).toBeInTheDocument();
    expect(screen.getByText(/Start with one persisted ledger row for the selected request ID/i)).toBeInTheDocument();
    expect(screen.getByText(/supporting runtime context for that same routed request investigation/i)).toBeInTheDocument();

    expect(await screen.findByRole("heading", { name: "Grounded follow-up guidance for the selected request" })).toBeInTheDocument();
    expect(screen.getByText(/bounded operator guidance for the selected-request investigation/i)).toBeInTheDocument();
    expect(screen.getByText(/not black-box optimization or a replacement for the persisted ledger row/i)).toBeInTheDocument();
    expect(await screen.findByText("Tighten cache similarity threshold")).toBeInTheDocument();
    expect(screen.getByText(/Raise the similarity threshold in policy preview before saving/i)).toBeInTheDocument();

    const selectedRequestSection = screen.getByRole("heading", { name: "Inspect one persisted ledger row before reading tenant context" }).closest("section");
    expect(selectedRequestSection).not.toBeNull();
    const selectedRequest = within(selectedRequestSection!);
    expect(selectedRequest.getByText(/Pick the request first\./i)).toBeInTheDocument();
    expect(selectedRequest.getByText(/The selected ledger row remains the authoritative persisted record/i)).toBeInTheDocument();
    expect(selectedRequest.getByText(/they do not overrule the selected request evidence/i)).toBeInTheDocument();
    expect(selectedRequest.getByText("Request detail")).toBeInTheDocument();
    expect(selectedRequest.getAllByText("req-123").length).toBeGreaterThanOrEqual(2);

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
