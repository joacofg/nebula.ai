import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ObservabilityPage from "./page";

const listTenants = vi.fn();
const listUsageLedger = vi.fn();
const getTenantRecommendations = vi.fn();

vi.mock("@/lib/admin-api", () => ({
  listTenants: (...args: unknown[]) => listTenants(...args),
  listUsageLedger: (...args: unknown[]) => listUsageLedger(...args),
  getTenantRecommendations: (...args: unknown[]) => getTenantRecommendations(...args),
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
        route_signals: null,
      },
    ]);
    getTenantRecommendations.mockResolvedValue({
      tenant_id: "tenant-alpha",
      generated_at: "2026-03-27T18:00:00Z",
      window_requests_evaluated: 30,
      calibration_summary: {
        tenant_id: "tenant-alpha",
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
          code: "cache-window-review",
          title: "Review cache aging window",
          priority: 2,
          category: "cache",
          summary: "Recent ledger-backed traffic suggests useful reuse, but long entry age may widen stale-response risk.",
          recommended_action: "Preview a lower max entry age in policy before saving any runtime change.",
          evidence: [
            { label: "Requests evaluated", value: "30" },
            { label: "Current max age", value: "168 hours" },
          ],
        },
      ],
      cache_summary: {
        enabled: true,
        similarity_threshold: 0.9,
        max_entry_age_hours: 168,
        runtime_status: "degraded",
        runtime_detail: "Qdrant is warming and may reduce cache consistency.",
        estimated_hit_rate: 0.38,
        avoided_premium_cost_usd: 0.84,
        insights: [
          {
            code: "cache-runtime-degraded",
            title: "Degraded cache runtime remains visible",
            level: "notice",
            summary: "Cache lookups still return value, but degraded runtime should be part of the operator explanation.",
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
            postgres: { status: "healthy", required: true, detail: "ready" },
            qdrant: { status: "degraded", required: false, detail: "warming" },
          },
        }),
      }),
    );
  });

  it("renders the integrated observability framing, calibration context, recommendation context, and cache controls summary", async () => {
    renderPage();

    expect(await screen.findByText("Persisted request evidence")).toBeInTheDocument();
    expect(screen.getByText(/public X-Request-ID and X-Nebula-\* headers/i)).toBeInTheDocument();
    expect(await screen.findByText("Next-best actions from recent tenant traffic")).toBeInTheDocument();
    expect(
      screen.getByText(/Recommendations are derived from recent ledger-backed traffic plus supporting runtime context/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/not black-box optimization/i)).toBeInTheDocument();
    expect(await screen.findByText("Tenant-scoped replay readiness context")).toBeInTheDocument();
    expect(screen.getByText(/derived from existing ledger metadata for the selected tenant/i)).toBeInTheDocument();
    expect(screen.getByText(/without turning Observability into a replacement for the persisted request record/i)).toBeInTheDocument();
    expect(screen.getAllByText("Recent eligible calibrated rows meet the tenant sufficiency threshold.")).toHaveLength(2);
    expect(screen.getByText("Eligible calibrated rows")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("Sufficiency threshold")).toBeInTheDocument();
    expect(await screen.findByText("Review cache aging window")).toBeInTheDocument();
    expect(screen.getByText(/Preview a lower max entry age in policy before saving any runtime change/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Cache effectiveness and runtime controls" })).toBeInTheDocument();
    expect(screen.getByText("Runtime detail:")).toBeInTheDocument();
    expect(screen.getByText(/Qdrant is warming and may reduce cache consistency/i)).toBeInTheDocument();
    expect(screen.getByText("Similarity threshold")).toBeInTheDocument();
    expect(screen.getByText("0.90")).toBeInTheDocument();
    expect(screen.getByText("Max entry age")).toBeInTheDocument();
    expect(screen.getAllByText("168 hours")).toHaveLength(2);
    expect(screen.getByRole("heading", { name: "Dependency health context" })).toBeInTheDocument();
    expect(screen.getByText(/Required dependency failures block confidence immediately/i)).toBeInTheDocument();
    expect(await screen.findAllByText("tenant-alpha")).toHaveLength(2);
    expect(await screen.findAllByText("Route target")).toHaveLength(3);
  });

  it("renders thin calibration evidence without inventing a separate analytics flow", async () => {
    getTenantRecommendations.mockResolvedValueOnce({
      tenant_id: "tenant-alpha",
      generated_at: "2026-03-27T18:00:00Z",
      window_requests_evaluated: 3,
      calibration_summary: {
        tenant_id: "tenant-alpha",
        scope: "tenant",
        state: "thin",
        state_reason: "Eligible calibrated routing evidence is still below the tenant sufficiency threshold.",
        generated_at: "2026-03-27T18:00:00Z",
        latest_eligible_request_at: "2026-03-27T16:00:00Z",
        latest_any_request_at: "2026-03-27T16:30:00Z",
        eligible_request_count: 3,
        sufficient_request_count: 3,
        thin_request_threshold: 5,
        staleness_threshold_hours: 24,
        excluded_request_count: 0,
        gated_request_count: 0,
        degraded_request_count: 0,
        excluded_reasons: [],
        gated_reasons: [],
        degraded_reasons: [],
      },
      recommendations: [],
      cache_summary: {
        enabled: true,
        similarity_threshold: 0.9,
        max_entry_age_hours: 168,
        runtime_status: "ready",
        runtime_detail: "Ready",
        estimated_hit_rate: 0.1,
        avoided_premium_cost_usd: 0.02,
        insights: [],
      },
    });

    renderPage();

    expect(await screen.findByText("thin")).toBeInTheDocument();
    expect(screen.getAllByText("Eligible calibrated routing evidence is still below the tenant sufficiency threshold.")).toHaveLength(2);
    expect(screen.getByText(/Keep using the ledger row and request ID correlation as the primary proof/i)).toBeInTheDocument();
    expect(screen.queryByText(/analytics/i)).not.toBeInTheDocument();
  });

  it("renders stale calibration evidence when the tenant window is no longer fresh", async () => {
    getTenantRecommendations.mockResolvedValueOnce({
      tenant_id: "tenant-alpha",
      generated_at: "2026-03-27T18:00:00Z",
      window_requests_evaluated: 11,
      calibration_summary: {
        tenant_id: "tenant-alpha",
        scope: "tenant",
        state: "stale",
        state_reason: "Eligible calibrated evidence exists but the newest row is outside the freshness window.",
        generated_at: "2026-03-27T18:00:00Z",
        latest_eligible_request_at: "2026-03-24T12:00:00Z",
        latest_any_request_at: "2026-03-27T17:00:00Z",
        eligible_request_count: 11,
        sufficient_request_count: 11,
        thin_request_threshold: 5,
        staleness_threshold_hours: 24,
        excluded_request_count: 0,
        gated_request_count: 0,
        degraded_request_count: 1,
        excluded_reasons: [],
        gated_reasons: [],
        degraded_reasons: [{ reason: "missing_route_signals", count: 1 }],
      },
      recommendations: [],
      cache_summary: {
        enabled: false,
        similarity_threshold: 0.9,
        max_entry_age_hours: 168,
        runtime_status: "unknown",
        runtime_detail: "Unavailable",
        estimated_hit_rate: 0,
        avoided_premium_cost_usd: 0,
        insights: [],
      },
    });

    renderPage();

    expect(await screen.findByText("stale")).toBeInTheDocument();
    expect(screen.getAllByText("Eligible calibrated evidence exists but the newest row is outside the freshness window.")).toHaveLength(2);
  });

  it("renders rollout-disabled calibration evidence when recent traffic is gated", async () => {
    getTenantRecommendations.mockResolvedValueOnce({
      tenant_id: "tenant-alpha",
      generated_at: "2026-03-27T18:00:00Z",
      window_requests_evaluated: 4,
      calibration_summary: {
        tenant_id: "tenant-alpha",
        scope: "tenant",
        state: "thin",
        state_reason: "Calibrated routing remained disabled for recent tenant traffic.",
        generated_at: "2026-03-27T18:00:00Z",
        latest_eligible_request_at: null,
        latest_any_request_at: "2026-03-27T17:00:00Z",
        eligible_request_count: 0,
        sufficient_request_count: 0,
        thin_request_threshold: 5,
        staleness_threshold_hours: 24,
        excluded_request_count: 0,
        gated_request_count: 4,
        degraded_request_count: 0,
        excluded_reasons: [],
        gated_reasons: [{ reason: "calibrated_routing_disabled", count: 4 }],
        degraded_reasons: [],
      },
      recommendations: [],
      cache_summary: {
        enabled: true,
        similarity_threshold: 0.9,
        max_entry_age_hours: 168,
        runtime_status: "ready",
        runtime_detail: "Ready",
        estimated_hit_rate: 0.25,
        avoided_premium_cost_usd: 0.12,
        insights: [],
      },
    });

    renderPage();

    expect(await screen.findAllByText("Calibrated routing remained disabled for recent tenant traffic.")).toHaveLength(2);
    expect(screen.getByText("Rollout-disabled rows")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
  });
});
