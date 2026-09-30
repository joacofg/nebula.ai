import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LedgerRequestDetail } from "@/components/ledger/ledger-request-detail";
import type { UsageLedgerRecord } from "@/lib/admin-api";
import { renderWithProviders } from "@/test/render";

const mockEntry: UsageLedgerRecord = {
  request_id: "req-embed-001",
  tenant_id: "tenant-embeddings",
  requested_model: "text-embedding-3-small",
  final_route_target: "embeddings",
  final_provider: "openai-compatible",
  fallback_used: true,
  cache_hit: false,
  response_model: "text-embedding-3-small",
  prompt_tokens: 24,
  completion_tokens: 0,
  total_tokens: 24,
  estimated_cost: 0.0005,
  latency_ms: 82,
  timestamp: "2026-03-17T01:02:03Z",
  terminal_status: "completed",
  route_reason: "embeddings_request",
  policy_outcome: "allowed",
  route_signals: null,
  message_type: "embeddings",
  evidence_retention_window: "30d",
  evidence_expires_at: "2026-04-16T01:02:03Z",
  metadata_minimization_level: "strict",
  metadata_fields_suppressed: [],
  governance_source: "tenant_policy",
};

function group(name: string) {
  return screen.getByRole("group", { name });
}

const heuristicSignals = {
  token_count: 842,
  complexity_tier: "medium",
  keyword_match: true,
  model_constraint: true,
  budget_proximity: null,
  route_mode: "calibrated",
  calibrated_routing: true,
  degraded_routing: false,
  score_components: { token_score: 1, keyword_bonus: 0.2, policy_bonus: 0.1, budget_penalty: 0, total_score: 1 },
};

describe("ledger-request-detail", () => {
  it("leads with cost and route, and folds the rest of the persisted evidence", () => {
    renderWithProviders(<LedgerRequestDetail entry={mockEntry} />);

    expect(screen.getByRole("heading", { name: /Pedido/ })).toHaveTextContent("req-embe");
    expect(group("Request ID")).toHaveTextContent("req-embed-001");
    expect(group("Costo estimado")).toHaveTextContent("USD 0.0005");
    expect(group("Tokens")).toHaveTextContent("24 + 0 = 24");
    expect(group("Modelo")).toHaveTextContent("text-embedding-3-small");
    expect(group("Proveedor")).toHaveTextContent("openai-compatible");
    expect(group("Ruta")).toHaveTextContent("embeddings");
    expect(group("Motivo")).toHaveTextContent("embeddings");
    expect(group("Estado")).toHaveTextContent("completado");
    expect(group("Latencia")).toHaveTextContent("82 ms");

    expect(screen.getByText("Evidencia completa")).toBeInTheDocument();
    expect(group("Tenant")).toHaveTextContent("tenant-embeddings");
    expect(group("Tipo de mensaje")).toHaveTextContent("embeddings");
    expect(group("Modelo pedido")).toHaveTextContent("text-embedding-3-small");
    expect(group("Política")).toHaveTextContent("allowed");
    expect(group("Retención")).toHaveTextContent("30d");
    expect(group("Minimización")).toHaveTextContent("strict");
    expect(group("Campos suprimidos")).toHaveTextContent("ninguno");
    expect(group("Fuente de gobierno")).toHaveTextContent("tenant_policy");
    expect(group("Fallback")).toHaveTextContent("sí");
    expect(group("Caché")).toHaveTextContent("no");
    expect(screen.queryByText(/authoritative/i)).not.toBeInTheDocument();
  });

  it("asks to pick a row when none is selected", () => {
    renderWithProviders(<LedgerRequestDetail entry={null} />);
    expect(screen.getByText("Elegir un pedido del ledger.")).toBeInTheDocument();
  });

  it("shows a dash for optional fields that are absent", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          request_id: "req-embed-002",
          final_provider: null,
          response_model: null,
          estimated_cost: null,
          latency_ms: null,
          route_reason: null,
          policy_outcome: null,
          metadata_fields_suppressed: undefined as unknown as string[],
        }}
      />,
    );
    for (const name of ["Costo estimado", "Modelo", "Proveedor", "Motivo", "Latencia", "Política"]) {
      expect(group(name)).toHaveTextContent("—");
    }
    expect(group("Campos suprimidos")).toHaveTextContent("ninguno");
  });

  it("explains a learned-router decision with the decision path", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          final_route_target: "premium",
          route_reason: "learned_router",
          route_signals: {
            tier: "economy",
            p_local: 0.41,
            p_economy: 0.95,
            quality_target: 0.95,
            operating_point: { tau_local: 0.82, tau_economy: 0.92 },
            learned_router: "v1",
          },
        }}
      />,
    );
    expect(screen.getByRole("heading", { name: "Por qué este nivel" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /economy elegido \(0\.95 ≥ 0\.92\)/ })).toBeInTheDocument();
  });

  it("renders the heuristic inspection with its additive score", () => {
    renderWithProviders(
      <LedgerRequestDetail entry={{ ...mockEntry, route_reason: "token_complexity", route_signals: heuristicSignals }} />,
    );
    expect(screen.getByText("Ruteo heurístico")).toBeInTheDocument();
    expect(group("Estado del ruteo")).toHaveTextContent("calibrado (score 1.00)");
    expect(group("Modo")).toHaveTextContent("calibrated");
    expect(group("Score")).toHaveTextContent("1.00");
    expect(group("Score por tokens")).toHaveTextContent("1.00");
    expect(group("Bono por palabra clave")).toHaveTextContent("0.20");
    expect(group("Bono de política")).toHaveTextContent("0.10");
    expect(group("Penalidad de presupuesto")).toHaveTextContent("0.00");
    expect(group("Tokens contados")).toHaveTextContent("842");
    expect(group("Complejidad")).toHaveTextContent("medium");
  });

  it("names degraded, rollout-disabled and unscored heuristic rows", () => {
    const { unmount } = renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          route_reason: "token_complexity",
          route_signals: { ...heuristicSignals, route_mode: "degraded", calibrated_routing: false, degraded_routing: true,
            score_components: { token_score: 0.6, keyword_bonus: 0, policy_bonus: 0, budget_penalty: 0, total_score: 0.6 } },
        }}
      />,
    );
    expect(group("Estado del ruteo")).toHaveTextContent("degradado (score 0.60)");
    unmount();

    const rollout = renderWithProviders(
      <LedgerRequestDetail
        entry={{ ...mockEntry, route_reason: "calibrated_routing_disabled", route_signals: { token_count: 144, complexity_tier: "low" } }}
      />,
    );
    expect(group("Estado del ruteo")).toHaveTextContent("rollout desactivado");
    expect(screen.queryByRole("group", { name: "Modo" })).not.toBeInTheDocument();
    rollout.unmount();

    renderWithProviders(
      <LedgerRequestDetail
        entry={{ ...mockEntry, route_reason: "explicit_premium_model", route_signals: { token_count: 61, complexity_tier: "low" } }}
      />,
    );
    expect(group("Estado del ruteo")).toHaveTextContent("sin score");
    expect(screen.queryByRole("group", { name: "Score" })).not.toBeInTheDocument();
  });

  it("reads a hard-budget downgrade from the policy outcome", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          final_route_target: "local",
          route_reason: "hard_budget_downgrade",
          policy_outcome:
            "hard_budget=exceeded(limit_usd=0.05,spent_usd=0.1,enforcement=downgrade);budget_action=downgraded_to_local",
        }}
      />,
    );
    expect(screen.getByText("Premium degradado a local")).toBeInTheDocument();
    expect(group("Acción")).toHaveTextContent("Degradado a local");
    expect(group("Límite duro")).toHaveTextContent("USD 0.05");
    expect(group("Gastado al decidir")).toHaveTextContent("USD 0.1");
    expect(group("Aplicación")).toHaveTextContent("Downgrade");
  });

  it("reads a hard-budget denial and a soft-budget advisory", () => {
    const denied = renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          final_route_target: "denied",
          terminal_status: "policy_denied",
          policy_outcome: "Tenant hard budget limit reached; premium routing is blocked (spent_usd=0.1, limit_usd=0.05).",
        }}
      />,
    );
    expect(screen.getByText("Pedido premium denegado por presupuesto")).toBeInTheDocument();
    expect(group("Motivo de la denegación")).toHaveTextContent("Tenant hard budget limit reached");
    expect(group("Límite duro")).toHaveTextContent("USD 0.05");
    denied.unmount();

    renderWithProviders(<LedgerRequestDetail entry={{ ...mockEntry, policy_outcome: "soft_budget=exceeded" }} />);
    expect(screen.getByText("Aviso de presupuesto blando")).toBeInTheDocument();
    expect(group("Presupuesto blando")).toHaveTextContent("Superado (solo aviso)");
  });

  it("omits routing sections when route_signals is null", () => {
    renderWithProviders(<LedgerRequestDetail entry={{ ...mockEntry, route_signals: null }} />);
    expect(screen.queryByText("Ruteo heurístico")).not.toBeInTheDocument();
    expect(screen.queryByText("Señales")).not.toBeInTheDocument();
  });
});
