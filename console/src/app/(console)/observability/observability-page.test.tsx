import { render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
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

function expectTextToAppearBefore(container: HTMLElement, first: string, second: string) {
  const content = container.textContent ?? "";
  const firstIndex = content.indexOf(first);
  const secondIndex = content.indexOf(second);

  expect(firstIndex).toBeGreaterThanOrEqual(0);
  expect(secondIndex).toBeGreaterThanOrEqual(0);
  expect(firstIndex).toBeLessThan(secondIndex);
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
        route_signals: {
          route_mode: "calibrated",
          calibrated_routing: true,
          degraded_routing: false,
          route_score: 0.91,
          token_count: 30,
          complexity_tier: "high",
          keyword_match: true,
          model_constraint: false,
          budget_proximity: 0.33,
          score_components: {
            total_score: 0.91,
            token_score: 0.66,
            keyword_bonus: 0.15,
            policy_bonus: 0.1,
            budget_penalty: 0,
          },
        },
        message_type: "chat",
        evidence_retention_window: "30d",
        evidence_expires_at: "2026-04-22T18:00:00Z",
        metadata_minimization_level: "standard",
        metadata_fields_suppressed: ["request_body", "response_body"],
        governance_source: "tenant_policy",
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

  it("leads with the filters, the ledger and the selected request", async () => {
    const { container } = renderPage();

    expect(await screen.findByRole("heading", { level: 1, name: "Observabilidad" })).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Filtros del ledger" })).toBeInTheDocument();
    const table = await screen.findByRole("table", { name: "Ledger de pedidos" });
    expect(within(table).getByRole("row", { selected: true })).toHaveTextContent("req-inte");
    expect(await screen.findByRole("heading", { name: /Pedido/ })).toHaveTextContent("req-integrated-001");
    expect(screen.getByRole("group", { name: "Costo estimado" })).toHaveTextContent("USD 0.0042");
    expectTextToAppearBefore(container, "req-inte", "Recomendaciones");
  });

  it("keeps tenant context in tabs: recommendations, cache, calibration and dependencies", async () => {
    const user = userEvent.setup();
    renderPage();

    const tabs = await screen.findByRole("tablist", { name: "Contexto del tenant" });
    expect(within(tabs).getAllByRole("tab").map((t) => t.textContent)).toEqual([
      "Recomendaciones",
      "Caché",
      "Calibración",
      "Dependencias",
    ]);
    expect(await screen.findByText("Review cache aging window")).toBeInTheDocument();
    expect(screen.getByText("Preview a lower max entry age in policy before saving any runtime change.")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "Caché" }));
    expect(await screen.findByRole("group", { name: "Tasa de aciertos estimada" })).toHaveTextContent("38 %");
    expect(screen.getByRole("group", { name: "Premium evitado" })).toHaveTextContent("USD 0.84");
    expect(screen.getByText("Degraded cache runtime remains visible")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "Calibración" }));
    expect(await screen.findByText("suficiente")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "Dependencias" }));
    expect(await screen.findByText("postgres")).toBeInTheDocument();
  });

  it("names stale tenant calibration in its tab", async () => {
    const user = userEvent.setup();
    const base = await getTenantRecommendations();
    getTenantRecommendations.mockResolvedValue({
      ...(base as object),
      calibration_summary: { ...(base as { calibration_summary: object }).calibration_summary, state: "stale" },
    });
    renderPage();
    await user.click(await screen.findByRole("tab", { name: "Calibración" }));
    expect(await screen.findByText("vencida")).toBeInTheDocument();
  });

  it("shows the ledger error instead of an empty table", async () => {
    listUsageLedger.mockRejectedValue(new Error("Ledger unavailable."));
    renderPage();
    await waitFor(() => expect(screen.getByText("Ledger unavailable.")).toBeInTheDocument());
  });

  it("offers the playground when the ledger is empty", async () => {
    listUsageLedger.mockResolvedValue([]);
    renderPage();
    await waitFor(() => expect(screen.getByText("No hay pedidos en este rango.")).toBeInTheDocument());
    expect(screen.getByText("Elegir un pedido del ledger.")).toBeInTheDocument();
  });

  it("says why the tenant filter is empty when the tenant list fails", async () => {
    listTenants.mockRejectedValue(new Error("Tenants unavailable."));
    renderPage();
    expect(await screen.findByText("Tenants unavailable.")).toBeInTheDocument();
  });
});
