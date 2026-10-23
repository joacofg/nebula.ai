import { screen, within } from "@testing-library/react";
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
  route_reason: "embeddings_direct",
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
  route_mode: "calibrated",
  calibrated_routing: true,
  degraded_routing: false,
  score_components: { token_score: 1, keyword_bonus: 0.2, policy_bonus: 0.1, total_score: 1 },
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
    expect(group("Ruta")).toHaveTextContent("Embeddings");
    expect(group("Motivo")).toHaveTextContent("embeddings");
    expect(group("Estado")).toHaveTextContent("completado");
    expect(group("Latencia")).toHaveTextContent("82 ms");

    expect(screen.getByText("Evidencia completa")).toBeInTheDocument();
    expect(group("Tenant")).toHaveTextContent("tenant-embeddings");
    expect(group("Tipo de mensaje")).toHaveTextContent("Embeddings");
    expect(group("Modelo pedido")).toHaveTextContent("text-embedding-3-small");
    // The policy outcome reads as the routing mode it applied; the gateway's own string stays one hover away.
    expect(group("Política")).toHaveTextContent("Automático");
    expect(within(group("Política")).getByText("Automático")).toHaveAttribute("title", "allowed");
    expect(group("Retención")).toHaveTextContent("30 días");
    expect(group("Minimización")).toHaveTextContent("estricta");
    expect(group("Campos suprimidos")).toHaveTextContent("ninguno");
    expect(group("Fuente de gobierno")).toHaveTextContent("política del tenant");
    expect(group("Fallback")).toHaveTextContent("sí");
    expect(group("Caché")).toHaveTextContent("no");
    expect(screen.queryByText(/authoritative/i)).not.toBeInTheDocument();
  });

  it("words the route and the governance values in Spanish and keeps a code it does not know", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          final_route_target: "denied",
          message_type: "chat",
          evidence_retention_window: "7d",
          metadata_minimization_level: "standard",
          metadata_fields_suppressed: ["route_signals", "request_body"],
        }}
      />,
    );

    expect(group("Ruta")).toHaveTextContent("Denegado");
    expect(group("Tipo de mensaje")).toHaveTextContent("Chat");
    expect(group("Retención")).toHaveTextContent("7 días");
    expect(group("Minimización")).toHaveTextContent("estándar");
    expect(group("Campos suprimidos")).toHaveTextContent("señales de ruteo, request_body");
  });

  it("keeps a retention window or minimization level it does not know as written", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{ ...mockEntry, evidence_retention_window: "1y" as never, metadata_minimization_level: "paranoid" as never }}
      />,
    );

    expect(group("Retención")).toHaveTextContent("1y");
    expect(group("Minimización")).toHaveTextContent("paranoid");
  });

  it("shows when the request happened on the viewer's clock, whether or not the gateway sent a zone", () => {
    const stampOf = (timestamp: string) => {
      const view = renderWithProviders(<LedgerRequestDetail entry={{ ...mockEntry, timestamp }} />);
      const text = screen.getByRole("heading", { name: /Pedido/ }).nextElementSibling?.textContent;
      view.unmount();
      return text;
    };

    expect(stampOf("2026-10-22T14:05:03")).toBe(stampOf("2026-10-22T14:05:03Z"));
    expect(stampOf("2026-10-22T14:05:03Z")).toMatch(/\d{2}:\d{2}:\d{2}/);
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
    expect(screen.getByRole("img", { name: /economy elegido \(p 0\.95 ≥ τ 0\.92\)/ })).toBeInTheDocument();
    // The detail column is narrow: the path is drawn 1:1 so its labels stay legible.
    expect(screen.getByRole("img", { name: /economy elegido/ })).toHaveAttribute("width");
  });

  it("names the tier that served a fallback row, not the one the router chose", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          final_route_target: "premium",
          response_model: "anthropic/claude-sonnet-4.5",
          fallback_used: true,
          route_reason: "local_provider_error_fallback",
          route_signals: {
            tier: "local",
            p_local: 0.9,
            p_economy: 0.95,
            quality_target: 0.95,
            operating_point: { tau_local: 0.82, tau_economy: 0.92 },
            learned_router: "v1",
          },
        }}
      />,
    );
    const heading = screen.getByRole("heading", { name: "Por qué este nivel" });
    expect(heading.parentElement).toHaveTextContent("frontier");
    expect(
      screen.getByText("Se sirvió con frontier por un fallback; el router había elegido local."),
    ).toBeInTheDocument();
  });

  it("falls back to the row's own tier for the badge on a legacy learned row without signals.tier", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          final_route_target: "premium",
          response_model: "anthropic/claude-haiku-4.5",
          route_reason: "learned_router",
          route_signals: {
            // No `tier`: the row is older than that signal. Its economy model identifies the tier.
            economy_model: "anthropic/claude-haiku-4.5",
            p_local: 0.1,
            p_economy: 0.2,
            quality_target: 0.95,
            operating_point: { tau_local: 0.82, tau_economy: 0.92 },
            learned_router: "v1",
          },
        }}
      />,
    );
    const header = screen.getByRole("heading", { name: "Por qué este nivel" }).parentElement;
    expect(header).toHaveTextContent("economy");
    expect(header).not.toHaveTextContent("frontier");
  });

  it("renders the heuristic inspection with its additive score", () => {
    renderWithProviders(
      <LedgerRequestDetail entry={{ ...mockEntry, route_reason: "token_complexity", route_signals: heuristicSignals }} />,
    );
    expect(screen.getByText("Ruteo heurístico")).toBeInTheDocument();
    expect(group("Estado del ruteo")).toHaveTextContent("calibrado (puntaje 1.00)");
    expect(group("Modo")).toHaveTextContent("calibrado");
    expect(group("Modo")).not.toHaveTextContent("calibrated");
    expect(group("Puntaje")).toHaveTextContent("1.00");
    expect(group("Puntaje por tokens")).toHaveTextContent("1.00");
    expect(group("Bono por palabra clave")).toHaveTextContent("0.20");
    expect(group("Bono de política")).toHaveTextContent("0.10");
    expect(group("Tokens contados")).toHaveTextContent("842");
    expect(group("Complejidad")).toHaveTextContent("media");
    expect(group("Complejidad")).not.toHaveTextContent("medium");
  });

  it("keeps a score mode or complexity it does not know as written", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          route_reason: "token_complexity",
          route_signals: { ...heuristicSignals, route_mode: "experimental", complexity_tier: "extreme" },
        }}
      />,
    );

    expect(group("Modo")).toHaveTextContent("experimental");
    expect(group("Complejidad")).toHaveTextContent("extreme");
  });

  it("ignores the retired budget keys that older ledger rows still carry", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          route_reason: "token_complexity",
          route_signals: {
            ...heuristicSignals,
            budget_proximity: 0.2,
            score_components: { ...heuristicSignals.score_components, budget_penalty: 0 },
          },
        }}
      />,
    );
    expect(group("Bono de política")).toHaveTextContent("0.10");
    expect(group("Tokens contados")).toHaveTextContent("842");
    expect(screen.queryByRole("group", { name: "Penalidad de presupuesto" })).not.toBeInTheDocument();
    expect(screen.queryByRole("group", { name: "Cercanía al presupuesto" })).not.toBeInTheDocument();
  });

  it("names degraded, rollout-disabled and unscored heuristic rows", () => {
    const { unmount } = renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          route_reason: "token_complexity",
          route_signals: { ...heuristicSignals, route_mode: "degraded", calibrated_routing: false, degraded_routing: true,
            score_components: { token_score: 0.6, keyword_bonus: 0, policy_bonus: 0, total_score: 0.6 } },
        }}
      />,
    );
    expect(group("Estado del ruteo")).toHaveTextContent("degradado (puntaje 0.60)");
    unmount();

    const rollout = renderWithProviders(
      <LedgerRequestDetail
        entry={{ ...mockEntry, route_reason: "calibrated_routing_disabled", route_signals: { token_count: 144, complexity_tier: "low" } }}
      />,
    );
    expect(group("Estado del ruteo")).toHaveTextContent("ruteo automático apagado");
    expect(screen.queryByRole("group", { name: "Modo" })).not.toBeInTheDocument();
    rollout.unmount();

    renderWithProviders(
      <LedgerRequestDetail
        entry={{ ...mockEntry, route_reason: "explicit_premium_model", route_signals: { token_count: 61, complexity_tier: "low" } }}
      />,
    );
    expect(group("Estado del ruteo")).toHaveTextContent("sin puntaje");
    expect(screen.queryByRole("group", { name: "Puntaje" })).not.toBeInTheDocument();
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
    expect(group("Límite duro")).toHaveTextContent("USD 0.0500");
    expect(group("Gastado al decidir")).toHaveTextContent("USD 0.1000");
    expect(group("Aplicación")).toHaveTextContent("degradar a local");
  });

  it("keeps a budget enforcement it does not know as the gateway wrote it", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          policy_outcome: "hard_budget=exceeded(limit_usd=0.05,spent_usd=0.1,enforcement=throttle)",
        }}
      />,
    );
    expect(group("Aplicación")).toHaveTextContent("throttle");
  });

  it("keeps an amount it cannot parse as the gateway wrote it", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          final_route_target: "local",
          route_reason: "hard_budget_downgrade",
          policy_outcome:
            "hard_budget=exceeded(limit_usd=unlimited,spent_usd=0.1,enforcement=downgrade);budget_action=downgraded_to_local",
        }}
      />,
    );
    expect(group("Límite duro")).toHaveTextContent("USD unlimited");
    expect(group("Gastado al decidir")).toHaveTextContent("USD 0.1000");
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
    expect(group("Motivo de la denegación")).toHaveTextContent(
      "Presupuesto duro alcanzado: ruteo premium bloqueado (gastado USD 0.1000, límite USD 0.0500)",
    );
    expect(group("Límite duro")).toHaveTextContent("USD 0.0500");
    expect(group("Gastado al decidir")).toHaveTextContent("USD 0.1000");
    denied.unmount();

    renderWithProviders(<LedgerRequestDetail entry={{ ...mockEntry, policy_outcome: "soft_budget=exceeded" }} />);
    expect(screen.getByText("Aviso de presupuesto blando")).toBeInTheDocument();
    expect(group("Presupuesto blando")).toHaveTextContent("Superado (solo aviso)");
  });

  it.each([
    [
      "Premium model 'openai/gpt-4o' is not allowed for this tenant.",
      "Modelo premium 'openai/gpt-4o' no permitido para este tenant",
    ],
    ["Request exceeds the tenant premium spend guardrail.", "El pedido supera el límite de costo por pedido"],
    ["Tenant policy requires premium-only routing.", "La política exige ruteo solo premium"],
    ["Tenant policy does not allow explicit premium routing.", "La política no permite pedir un modelo premium"],
    ["Tenant policy restricts this request to local routing only.", "La política restringe el pedido a ruteo solo local"],
    ["Tenant hard budget limit reached", "Presupuesto duro alcanzado: ruteo premium bloqueado"],
  ])("reads the denial %j in Spanish from the policy outcome", (english, spanish) => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          final_route_target: "denied",
          terminal_status: "policy_denied",
          policy_outcome: `routing_mode=auto;denied=${english};outcome_evidence=thin(eligible=0,sufficient=0)`,
        }}
      />,
    );

    const reason = group("Motivo de la denegación");
    expect(reason).toHaveTextContent(spanish);
    // The gateway's own sentence stays one hover away, for whoever has to search the logs for it.
    expect(within(reason).getByText(spanish)).toHaveAttribute("title", english);
  });

  it.each([
    [
      "routing_mode=premium_only;denied=Tenant policy requires premium-only routing.;outcome_evidence=thin(eligible=0,sufficient=0)",
      "Solo premium, denegado",
    ],
    ["routing_mode=local_only;denied=Tenant policy restricts this request to local routing only.", "Solo local, denegado"],
    ["routing_mode=local_only", "Solo local"],
    ["denied=Premium model 'openai/gpt-4o' is not allowed for this tenant.", "Automático, denegado"],
    ["soft_budget=exceeded;outcome_evidence=sufficient(eligible=7,sufficient=7)", "Automático"],
  ])("words the policy outcome %j as the mode it applied, not as the raw composite", (outcome, label) => {
    renderWithProviders(<LedgerRequestDetail entry={{ ...mockEntry, policy_outcome: outcome }} />);

    const policy = group("Política");
    expect(policy).toHaveTextContent(label);
    expect(policy).not.toHaveTextContent("routing_mode");
    expect(policy).not.toHaveTextContent("outcome_evidence");
    expect(within(policy).getByText(label)).toHaveAttribute("title", outcome);
  });

  it.each([
    ["the hard budget", "Tenant hard budget limit reached"],
    ["the per-request cap", "Request exceeds the tenant premium spend guardrail."],
  ])("files a denial by %s under Presupuesto, with its reason once", (_kind, sentence) => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          final_route_target: "denied",
          terminal_status: "policy_denied",
          policy_outcome: `routing_mode=auto;denied=${sentence};outcome_evidence=thin(eligible=0,sufficient=0)`,
        }}
      />,
    );

    expect(screen.getByRole("heading", { name: "Presupuesto" })).toBeInTheDocument();
    expect(screen.getByText("Pedido premium denegado por presupuesto")).toBeInTheDocument();
    expect(screen.getAllByRole("group", { name: "Motivo de la denegación" })).toHaveLength(1);
  });

  it.each([
    [
      "a model that is not allowed",
      "Premium model 'openai/gpt-4o' is not allowed for this tenant.",
      "Modelo premium 'openai/gpt-4o' no permitido para este tenant",
    ],
    ["premium-only routing", "Tenant policy requires premium-only routing.", "La política exige ruteo solo premium"],
    [
      "explicit premium routing under local-only",
      "Tenant policy does not allow explicit premium routing.",
      "La política no permite pedir un modelo premium",
    ],
    [
      "local-only routing",
      "Tenant policy restricts this request to local routing only.",
      "La política restringe el pedido a ruteo solo local",
    ],
    // A sentence it does not know stays as the gateway wrote it.
    ["a reason it does not know", "Something new was denied.", "Something new was denied."],
  ])("does not call a denial for %s a budget denial, and shows its reason on its own line", (_kind, sentence, spanish) => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          final_route_target: "denied",
          terminal_status: "policy_denied",
          policy_outcome: `routing_mode=auto;denied=${sentence};outcome_evidence=thin(eligible=0,sufficient=0)`,
        }}
      />,
    );

    expect(screen.queryByRole("heading", { name: "Presupuesto" })).not.toBeInTheDocument();
    expect(screen.queryByText(/denegado por presupuesto/)).not.toBeInTheDocument();
    expect(screen.getAllByRole("group", { name: "Motivo de la denegación" })).toHaveLength(1);
    expect(group("Motivo de la denegación")).toHaveTextContent(spanish);
  });

  it("keeps the exceeded hard budget under Presupuesto without blaming it for a denial it did not cause", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          final_route_target: "denied",
          terminal_status: "policy_denied",
          policy_outcome:
            "hard_budget=exceeded(limit_usd=0.05,spent_usd=0.1,enforcement=deny);denied=Premium model 'openai/gpt-4o' is not allowed for this tenant.",
        }}
      />,
    );

    expect(screen.getByRole("heading", { name: "Presupuesto" })).toBeInTheDocument();
    expect(screen.getByText("Presupuesto duro alcanzado")).toBeInTheDocument();
    expect(screen.queryByText("Pedido premium denegado por presupuesto")).not.toBeInTheDocument();
    expect(group("Gastado al decidir")).toHaveTextContent("USD 0.1000");
    expect(group("Motivo de la denegación")).toHaveTextContent("Modelo premium 'openai/gpt-4o' no permitido para este tenant");
  });

  it("keeps a denial it does not know as the gateway wrote it", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{ ...mockEntry, final_route_target: "denied", policy_outcome: "routing_mode=auto;denied=Something new was denied." }}
      />,
    );

    const reason = group("Motivo de la denegación");
    expect(reason).toHaveTextContent("Something new was denied.");
    expect(within(reason).getByText("Something new was denied.")).not.toHaveAttribute("title");
  });

  it("omits routing sections when route_signals is null", () => {
    renderWithProviders(<LedgerRequestDetail entry={{ ...mockEntry, route_signals: null }} />);
    expect(screen.queryByText("Ruteo heurístico")).not.toBeInTheDocument();
    expect(screen.queryByText("Señales")).not.toBeInTheDocument();
  });
});
