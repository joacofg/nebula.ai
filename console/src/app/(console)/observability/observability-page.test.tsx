import type { ReactNode } from "react";

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SelectedTenantProvider } from "@/lib/selected-tenant";
import { createTestQueryClient } from "@/test/render";

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
  const queryClient = createTestQueryClient();

  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <SelectedTenantProvider>{children}</SelectedTenantProvider>
      </QueryClientProvider>
    );
  }

  return render(<ObservabilityPage />, { wrapper: Wrapper });
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
          score_components: {
            total_score: 0.91,
            token_score: 0.66,
            keyword_bonus: 0.15,
            policy_bonus: 0.1,
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
    expect(within(table).getByRole("row", { current: true })).toHaveTextContent("req-inte");
    expect(await screen.findByRole("heading", { name: /Pedido/ })).toHaveTextContent("req-inte");
    expect(screen.getByRole("group", { name: "Costo estimado" })).toHaveTextContent("USD 0.0042");
    expectTextToAppearBefore(container, "req-inte", "Recomendaciones");
  });

  it("refreshes the ledger and the tenant context from the page header, outside the filters", async () => {
    const user = userEvent.setup();
    const { container } = renderPage();
    await screen.findByRole("table", { name: "Ledger de pedidos" });
    await waitFor(() => expect(getTenantRecommendations).toHaveBeenCalled());
    const ledgerCalls = listUsageLedger.mock.calls.length;
    const recommendationCalls = getTenantRecommendations.mock.calls.length;

    const header = container.querySelector("header") as HTMLElement;
    expect(within(screen.getByRole("group", { name: "Filtros del ledger" })).queryByRole("button")).not.toBeInTheDocument();
    await user.click(within(header).getByRole("button", { name: "Actualizar" }));

    await waitFor(() => expect(listUsageLedger.mock.calls.length).toBe(ledgerCalls + 1));
    await waitFor(() => expect(getTenantRecommendations.mock.calls.length).toBe(recommendationCalls + 1));
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
    expect(screen.getByRole("group", { name: "Premium evitado" })).toHaveTextContent("USD 0.8400");
    expect(screen.getByText("Degraded cache runtime remains visible")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "Calibración" }));
    expect(await screen.findByText("suficiente")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "Dependencias" }));
    expect(await screen.findByText("postgres")).toBeInTheDocument();
  });

  it("says the gateway is unreachable in the dependencies tab", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "gateway_unreachable" }), { status: 503 })),
    );
    renderPage();

    await user.click(await screen.findByRole("tab", { name: "Dependencias" }));
    expect(await screen.findByText("No se pudo conectar con el gateway.")).toBeInTheDocument();
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

  it("shows the recommendations failure in the cache and calibration tabs too", async () => {
    const user = userEvent.setup();
    getTenantRecommendations.mockRejectedValue(new Error("Recommendations unavailable."));
    renderPage();

    await user.click(await screen.findByRole("tab", { name: "Caché" }));
    expect(await screen.findByText("Recommendations unavailable.")).toBeInTheDocument();
    expect(screen.queryByText("Elegir un tenant para ver su caché.")).not.toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "Calibración" }));
    expect(await screen.findByText("Recommendations unavailable.")).toBeInTheDocument();
    expect(screen.queryByText("Elegir un tenant para ver su calibración.")).not.toBeInTheDocument();
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

  it("still loads the ledger when the tenant list fails", async () => {
    listTenants.mockRejectedValue(new Error("Tenants unavailable."));
    renderPage();

    expect(await screen.findByText("Tenants unavailable.")).toBeInTheDocument();
    const table = await screen.findByRole("table", { name: "Ledger de pedidos" });
    expect(within(table).getByRole("row", { name: /req-integrated-001/ })).toBeInTheDocument();
    // With no tenant list there is no default tenant to read: every tenant's rows.
    expect(listUsageLedger).toHaveBeenLastCalledWith("nebula-admin-key", expect.objectContaining({ tenantId: "" }));
  });

  describe("ledger filters", () => {
    beforeEach(() => {
      listUsageLedger.mockClear();
    });

    async function settledFilters() {
      await screen.findByRole("table", { name: "Ledger de pedidos" });
      return within(screen.getByRole("group", { name: "Filtros del ledger" }));
    }

    it("sends the tier the operator picks and none until then", async () => {
      const user = userEvent.setup();
      renderPage();
      const filters = await settledFilters();
      expect(listUsageLedger.mock.calls.every(([, sent]) => !sent.tier)).toBe(true);

      await user.selectOptions(filters.getByLabelText("Nivel"), "economy");

      await waitFor(() =>
        expect(listUsageLedger).toHaveBeenLastCalledWith("nebula-admin-key", expect.objectContaining({ tier: "economy" })),
      );
    });

    it("sends the status the gateway records for an abandoned stream", async () => {
      const user = userEvent.setup();
      renderPage();
      const filters = await settledFilters();

      await user.selectOptions(filters.getByLabelText("Estado"), "client_disconnected");

      await waitFor(() =>
        expect(listUsageLedger).toHaveBeenLastCalledWith(
          "nebula-admin-key",
          expect.objectContaining({ terminalStatus: "client_disconnected" }),
        ),
      );
    });

    it("sends the dates as the UTC instants of the local times the operator typed", async () => {
      renderPage();
      const filters = await settledFilters();

      fireEvent.change(filters.getByLabelText("Desde"), { target: { value: "2026-10-22T10:00" } });
      fireEvent.change(filters.getByLabelText("Hasta"), { target: { value: "2026-10-22T18:30" } });

      await waitFor(() =>
        expect(listUsageLedger).toHaveBeenLastCalledWith(
          "nebula-admin-key",
          expect.objectContaining({
            fromTimestamp: new Date("2026-10-22T10:00").toISOString(),
            toTimestamp: new Date("2026-10-22T18:30").toISOString(),
          }),
        ),
      );
      // The inputs keep what was typed, in the operator's clock.
      expect(filters.getByLabelText("Desde")).toHaveValue("2026-10-22T10:00");
      expect(filters.getByLabelText("Hasta")).toHaveValue("2026-10-22T18:30");
    });

    it("sends no date while the input is cleared", async () => {
      renderPage();
      const filters = await settledFilters();
      fireEvent.change(filters.getByLabelText("Desde"), { target: { value: "2026-10-22T10:00" } });
      await waitFor(() =>
        expect(listUsageLedger).toHaveBeenLastCalledWith("nebula-admin-key", expect.objectContaining({ fromTimestamp: expect.any(String) })),
      );

      fireEvent.change(filters.getByLabelText("Desde"), { target: { value: "" } });

      await waitFor(() =>
        expect(listUsageLedger).toHaveBeenLastCalledWith("nebula-admin-key", expect.objectContaining({ fromTimestamp: "" })),
      );
    });
  });

  describe("cost summary", () => {
    const row = (requestId: string, cost: number | null) => ({
      request_id: requestId,
      tenant_id: "tenant-alpha",
      requested_model: "gpt-4o-mini",
      final_route_target: "premium",
      final_provider: "openai-compatible",
      fallback_used: false,
      cache_hit: false,
      response_model: "gpt-4o-mini",
      prompt_tokens: 1,
      completion_tokens: 1,
      total_tokens: 2,
      estimated_cost: cost,
      latency_ms: 100,
      timestamp: "2026-03-23T18:00:00Z",
      terminal_status: "completed",
      route_reason: "learned_router",
      policy_outcome: "allowed",
      route_signals: null,
      message_type: "chat",
      evidence_retention_window: "30d",
      evidence_expires_at: null,
      metadata_minimization_level: "standard",
      metadata_fields_suppressed: [],
      governance_source: "tenant_policy",
    });

    it("says how many requests the cost adds up and what 1000 of them cost", async () => {
      listUsageLedger.mockResolvedValue([row("req-a", 0.0042), row("req-b", 0.0018)]);
      renderPage();

      expect(await screen.findByText("USD 0.0060 en 2 pedidos")).toBeInTheDocument();
      expect(screen.getByText("USD 3.00 / 1000")).toBeInTheDocument();
    });

    it("counts a request with no recorded cost as zero, in the sum and in the number of requests", async () => {
      listUsageLedger.mockResolvedValue([row("req-a", 0.0042), row("req-b", null)]);
      renderPage();

      expect(await screen.findByText("USD 0.0042 en 2 pedidos")).toBeInTheDocument();
      expect(screen.getByText("USD 2.10 / 1000")).toBeInTheDocument();
    });

    it("counts a single request in the singular", async () => {
      renderPage();

      expect(await screen.findByText("USD 0.0042 en 1 pedido")).toBeInTheDocument();
      expect(screen.getByText("USD 4.20 / 1000")).toBeInTheDocument();
    });

    it("has no cost per 1000 when there are no requests to average", async () => {
      listUsageLedger.mockResolvedValue([]);
      renderPage();

      expect(await screen.findByText("USD 0.0000 en 0 pedidos")).toBeInTheDocument();
      expect(screen.queryByText(/\/ 1000/)).not.toBeInTheDocument();
    });

    it("shows a dash instead of a cost until the ledger arrives", () => {
      listUsageLedger.mockReturnValue(new Promise(() => {}));
      renderPage();

      expect(screen.getByText("Costo").parentElement).toHaveTextContent(/^Costo—$/);
    });
  });

  describe("tenant scope", () => {
    beforeEach(() => {
      listUsageLedger.mockClear();
      getTenantRecommendations.mockClear();
      listTenants.mockResolvedValue([
        { id: "tenant-alpha", name: "Tenant Alpha" },
        { id: "tenant-bravo", name: "Tenant Bravo" },
      ]);
    });

    function tenantFilter() {
      return within(screen.getByRole("group", { name: "Filtros del ledger" })).getByLabelText("Tenant");
    }

    it("starts on the shared tenant and lets the operator pick Todos los tenants", async () => {
      const user = userEvent.setup();
      renderPage();

      await waitFor(() => expect(tenantFilter()).toHaveValue("tenant-alpha"));
      await user.selectOptions(tenantFilter(), "");

      expect(tenantFilter()).toHaveValue("");
      await waitFor(() =>
        expect(listUsageLedger).toHaveBeenLastCalledWith("nebula-admin-key", expect.objectContaining({ tenantId: "" })),
      );
      // Settled: the all-tenants ledger has loaded and drawn, so every effect it triggered has run.
      await screen.findByRole("table", { name: "Ledger de pedidos" });
      // The default selection does not come back over the operator's choice.
      expect(tenantFilter()).toHaveValue("");
      expect(listUsageLedger).toHaveBeenLastCalledWith("nebula-admin-key", expect.objectContaining({ tenantId: "" }));
    });

    it("keeps Todos los tenants when the page renders again", async () => {
      const user = userEvent.setup();
      const view = renderPage();
      await waitFor(() => expect(tenantFilter()).toHaveValue("tenant-alpha"));
      await user.selectOptions(tenantFilter(), "");

      view.rerender(<ObservabilityPage />);

      expect(tenantFilter()).toHaveValue("");
    });

    it("shares the tenant picked here with the other pages, and starts on the one picked there", async () => {
      const user = userEvent.setup();
      const view = renderPage();
      await waitFor(() => expect(tenantFilter()).toHaveValue("tenant-alpha"));
      await user.selectOptions(tenantFilter(), "tenant-bravo");

      view.rerender(<div />);
      view.rerender(<ObservabilityPage />);

      await waitFor(() => expect(tenantFilter()).toHaveValue("tenant-bravo"));
      await waitFor(() =>
        expect(getTenantRecommendations).toHaveBeenLastCalledWith("nebula-admin-key", "tenant-bravo"),
      );
    });

    it("does not read the ledger of every tenant while the tenant list loads", async () => {
      renderPage();
      await waitFor(() => expect(tenantFilter()).toHaveValue("tenant-alpha"));
      await screen.findByRole("table", { name: "Ledger de pedidos" });
      for (const call of listUsageLedger.mock.calls) {
        expect(call[1]).toEqual(expect.objectContaining({ tenantId: "tenant-alpha" }));
      }
    });

    it("asks for no tenant context and shows the empty ledger when there are no tenants", async () => {
      listTenants.mockResolvedValue([]);
      listUsageLedger.mockResolvedValue([]);
      renderPage();

      await waitFor(() => expect(screen.getByText("No hay pedidos en este rango.")).toBeInTheDocument());
      expect(getTenantRecommendations).not.toHaveBeenCalled();
    });
  });
});
