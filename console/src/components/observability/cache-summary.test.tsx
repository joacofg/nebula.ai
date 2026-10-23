import { screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CacheSummary } from "@/components/observability/cache-summary";
import type { CacheControlSummary } from "@/lib/admin-api";
import { renderWithProviders } from "@/test/render";

const base: CacheControlSummary = {
  enabled: true,
  similarity_threshold: 0.9,
  max_entry_age_hours: 168,
  runtime_status: "ready",
  runtime_detail: "Qdrant disponible.",
  estimated_hit_rate: 0.38,
  avoided_premium_cost_usd: 0.012345,
  insights: [],
};

describe("CacheSummary", () => {
  it("shows the avoided premium cost with four decimals, as a hit can avoid fractions of a cent", () => {
    renderWithProviders(<CacheSummary cache={base} />);
    expect(screen.getByRole("group", { name: "Premium evitado" })).toHaveTextContent("USD 0.0123");
  });

  it("shows zero avoided cost as USD 0.0000", () => {
    renderWithProviders(<CacheSummary cache={{ ...base, avoided_premium_cost_usd: 0 }} />);
    expect(screen.getByRole("group", { name: "Premium evitado" })).toHaveTextContent("USD 0.0000");
  });

  it("names the runtime status in Spanish and keeps one it does not know as it came", () => {
    const { rerender } = renderWithProviders(<CacheSummary cache={{ ...base, runtime_status: "not_ready" }} />);
    expect(screen.getByRole("group", { name: "Estado en runtime" })).toHaveTextContent("No listo");

    rerender(<CacheSummary cache={{ ...base, runtime_status: "on_fire" as CacheControlSummary["runtime_status"] }} />);
    expect(screen.getByRole("group", { name: "Estado en runtime" })).toHaveTextContent("on_fire");
  });

  it("says in Spanish what each insight is, from its code", () => {
    renderWithProviders(
      <CacheSummary
        cache={{
          ...base,
          runtime_status: "degraded",
          insights: [
            {
              code: "cache_runtime_degraded",
              title: "Semantic cache degraded",
              level: "warning",
              summary: "Qdrant unavailable: boom",
              evidence: [
                { label: "runtime_status", value: "degraded" },
                { label: "cache_enabled", value: "true" },
              ],
            },
            {
              code: "cache_effectiveness_window",
              title: "Recent cache effectiveness",
              level: "info",
              summary: "Recent cache hit rate is 38% across 12 ledger-backed requests.",
              evidence: [
                { label: "cache_hits", value: "5" },
                { label: "window_requests", value: "12" },
                { label: "avoided_premium_cost_usd", value: "0.012345" },
              ],
            },
          ],
        }}
      />,
    );

    const degraded = screen.getByRole("heading", { name: "Caché semántico degradado" }).closest("article");
    expect(degraded).not.toBeNull();
    const degradedView = within(degraded as HTMLElement);
    expect(degradedView.getByText("alerta")).toBeInTheDocument();
    expect(degradedView.getByRole("group", { name: "Estado en runtime" })).toHaveTextContent("Degradado");
    expect(degradedView.getByRole("group", { name: "Caché activada" })).toHaveTextContent("sí");

    const effectiveness = screen.getByRole("heading", { name: "Efectividad reciente del caché" }).closest("article");
    const effectivenessView = within(effectiveness as HTMLElement);
    expect(effectivenessView.getByRole("group", { name: "Aciertos" })).toHaveTextContent("5");
    expect(effectivenessView.getByRole("group", { name: "Pedidos en la ventana" })).toHaveTextContent("12");
    expect(effectivenessView.getByRole("group", { name: "Premium evitado" })).toHaveTextContent("USD 0.0123");

    // No English from the gateway is left on screen for an insight it knows.
    expect(screen.queryByText("Semantic cache degraded")).not.toBeInTheDocument();
    expect(screen.queryByText("Recent cache effectiveness")).not.toBeInTheDocument();
    expect(screen.queryByText(/ledger-backed/)).not.toBeInTheDocument();
    expect(screen.queryByText("Qdrant unavailable: boom")).not.toBeInTheDocument();
  });

  it("reads a disabled cache's evidence as no", () => {
    renderWithProviders(
      <CacheSummary
        cache={{
          ...base,
          enabled: false,
          insights: [
            {
              code: "cache_policy_disabled",
              title: "Semantic cache disabled",
              level: "notice",
              summary: "Semantic cache collection is reachable.",
              evidence: [{ label: "cache_enabled", value: "false" }],
            },
          ],
        }}
      />,
    );

    const article = screen.getByRole("heading", { name: "Caché semántico desactivado" }).closest("article");
    const view = within(article as HTMLElement);
    expect(view.getByText("aviso")).toBeInTheDocument();
    expect(view.getByRole("group", { name: "Caché activada" })).toHaveTextContent("no");
  });

  it("shows an insight with a code it does not know exactly as the gateway sent it", () => {
    renderWithProviders(
      <CacheSummary
        cache={{
          ...base,
          insights: [
            {
              code: "cache-health-watch",
              title: "Watch degraded cache runtime",
              level: "notice",
              summary: "Recent cache reuse remains valuable.",
              evidence: [{ label: "Runtime status", value: "degraded" }],
            },
          ],
        }}
      />,
    );

    const article = screen.getByRole("heading", { name: "Watch degraded cache runtime" }).closest("article");
    const view = within(article as HTMLElement);
    expect(view.getByText("Recent cache reuse remains valuable.")).toBeInTheDocument();
    expect(view.getByRole("group", { name: "Runtime status" })).toHaveTextContent("degraded");
  });

  it("keeps an evidence value it cannot read as it came", () => {
    renderWithProviders(
      <CacheSummary
        cache={{
          ...base,
          insights: [
            {
              code: "cache_effectiveness_window",
              title: "Recent cache effectiveness",
              level: "info",
              summary: "Recent cache hit rate is 0% across 0 ledger-backed requests.",
              evidence: [
                { label: "avoided_premium_cost_usd", value: "n/a" },
                { label: "cache_enabled", value: "maybe" },
                { label: "runtime_status", value: "on_fire" },
              ],
            },
          ],
        }}
      />,
    );

    const article = screen.getByRole("heading", { name: "Efectividad reciente del caché" }).closest("article");
    const view = within(article as HTMLElement);
    expect(view.getByRole("group", { name: "Premium evitado" })).toHaveTextContent("n/a");
    expect(view.getByRole("group", { name: "Caché activada" })).toHaveTextContent("maybe");
    expect(view.getByRole("group", { name: "Estado en runtime" })).toHaveTextContent("on_fire");
  });

  it("says so when the window has no insights", () => {
    renderWithProviders(<CacheSummary cache={base} />);
    expect(screen.getByText("Sin observaciones del caché en esta ventana.")).toBeInTheDocument();
  });
});
