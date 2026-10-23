import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CalibrationSummary } from "@/components/observability/calibration-summary";
import type { CalibrationEvidenceSummary } from "@/lib/admin-api";
import { renderWithProviders } from "@/test/render";

const base: CalibrationEvidenceSummary = {
  tenant_id: "tenant-a",
  scope: "tenant",
  state: "sufficient",
  state_reason: "Recent eligible calibrated rows meet the tenant sufficiency threshold.",
  generated_at: "2026-03-28T00:00:00Z",
  latest_eligible_request_at: "2026-03-27T12:00:00Z",
  latest_any_request_at: "2026-03-27T12:00:00Z",
  eligible_request_count: 7,
  sufficient_request_count: 7,
  thin_request_threshold: 5,
  staleness_threshold_hours: 24,
  excluded_request_count: 1,
  gated_request_count: 0,
  degraded_request_count: 1,
  excluded_reasons: [{ reason: "policy_forced_route", count: 1 }],
  gated_reasons: [],
  degraded_reasons: [{ reason: "missing_route_signals", count: 1 }],
};

function group(name: string) {
  return screen.getByRole("group", { name });
}

describe("CalibrationSummary", () => {
  it("states sufficient evidence with its counts", () => {
    renderWithProviders(<CalibrationSummary summary={base} />);
    expect(screen.getByText("suficiente")).toBeInTheDocument();
    expect(screen.getByText("La evidencia del tenant alcanza para el ruteo calibrado.")).toBeInTheDocument();
    expect(group("Filas elegibles")).toHaveTextContent("7 de 5 necesarias");
    expect(group("Filas degradadas")).toHaveTextContent("1 (sin señales de ruteo (1))");
    // A code the labels do not know (yet) stays as the gateway sent it, never title-cased English.
    expect(group("Filas excluidas")).toHaveTextContent("policy_forced_route (1)");
  });

  it("names the reasons in Spanish when the labels know them", () => {
    renderWithProviders(
      <CalibrationSummary
        summary={{
          ...base,
          excluded_request_count: 3,
          excluded_reasons: [
            { reason: "rate_limited", count: 2 },
            { reason: "explicit_model_override", count: 1 },
          ],
        }}
      />,
    );
    expect(group("Filas excluidas")).toHaveTextContent("3 (límite de pedidos (2), modelo explícito (1))");
  });

  it("names every code the gateway counts rows under, none left raw", () => {
    renderWithProviders(
      <CalibrationSummary
        summary={{
          ...base,
          excluded_request_count: 3,
          excluded_reasons: [
            { reason: "explicit_model_override", count: 2 },
            { reason: "policy_forced_routing", count: 1 },
          ],
          degraded_request_count: 3,
          degraded_reasons: [
            { reason: "missing_route_signals", count: 2 },
            { reason: "degraded_replay_signals", count: 1 },
          ],
        }}
      />,
    );
    expect(group("Filas excluidas")).toHaveTextContent("3 (modelo explícito (2), ruteo forzado por la política (1))");
    expect(group("Filas degradadas")).toHaveTextContent("3 (sin señales de ruteo (2), señales incompletas (1))");
    expect(screen.queryByText(/_/)).not.toBeInTheDocument();
  });

  it("says when calibrated routing is still gated by the operator", () => {
    renderWithProviders(
      <CalibrationSummary
        summary={{
          ...base,
          state: "thin",
          eligible_request_count: 0,
          gated_request_count: 3,
          gated_reasons: [{ reason: "calibrated_routing_disabled", count: 3 }],
          degraded_request_count: 0,
          degraded_reasons: [],
          excluded_request_count: 0,
          excluded_reasons: [],
          latest_eligible_request_at: null,
        }}
      />,
    );
    expect(screen.getByText("ruteo automático apagado")).toBeInTheDocument();
    expect(screen.getByText("Hay tráfico, pero el ruteo automático sigue apagado por el operador.")).toBeInTheDocument();
    expect(group("Filas con ruteo automático apagado")).toHaveTextContent("3 (ruteo automático apagado (3))");
    expect(screen.queryByText(/rollout/i)).not.toBeInTheDocument();
    expect(group("Última fila elegible")).toHaveTextContent("Sin filas elegibles");
  });

  it("names degraded, stale and thin evidence", () => {
    const degraded = renderWithProviders(<CalibrationSummary summary={{ ...base, state: "degraded" }} />);
    expect(screen.getByText("degradada")).toBeInTheDocument();
    degraded.unmount();

    const stale = renderWithProviders(<CalibrationSummary summary={{ ...base, state: "stale" }} />);
    expect(screen.getByText("vencida")).toBeInTheDocument();
    expect(group("Umbral de vencimiento")).toHaveTextContent("24 h");
    stale.unmount();

    renderWithProviders(<CalibrationSummary summary={{ ...base, state: "thin", eligible_request_count: 2, gated_request_count: 0 }} />);
    expect(screen.getByText("escasa")).toBeInTheDocument();
    expect(group("Filas elegibles")).toHaveTextContent("2 de 5 necesarias");
  });
});
