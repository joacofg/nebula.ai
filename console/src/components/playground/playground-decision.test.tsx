import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PlaygroundDecision } from "@/components/playground/playground-decision";
import type { UsageLedgerRecord } from "@/lib/admin-api";

function entry(overrides: Partial<UsageLedgerRecord> = {}): UsageLedgerRecord {
  return {
    request_id: "req-1",
    tenant_id: "default",
    requested_model: "nebula-auto",
    final_route_target: "premium",
    final_provider: "openai-compatible",
    fallback_used: false,
    cache_hit: false,
    response_model: "anthropic/claude-haiku-4.5",
    prompt_tokens: 12,
    completion_tokens: 30,
    total_tokens: 42,
    estimated_cost: 0.001,
    latency_ms: 900,
    timestamp: "2026-09-30T12:00:00Z",
    terminal_status: "completed",
    route_reason: "learned_router",
    policy_outcome: "allowed",
    route_signals: {
      tier: "economy",
      p_local: 0.69,
      p_economy: 0.91,
      quality_target: 0.9,
      operating_point: { tau_local: 0.76, tau_economy: 0.9, quality: 0.903, cost_per_prompt: 0.001 },
      learned_router: "v1",
      token_count: 12,
      complexity_tier: "low",
    },
    message_type: "chat",
    evidence_retention_window: "30d",
    evidence_expires_at: null,
    metadata_minimization_level: "standard",
    metadata_fields_suppressed: [],
    governance_source: "tenant_policy",
    ...overrides,
  };
}

function panelText(container: HTMLElement) {
  return container.textContent ?? "";
}

describe("PlaygroundDecision", () => {
  it("explains a learned-router decision step by step", () => {
    const { container } = render(<PlaygroundDecision entry={entry()} routeTier="economy" />);

    expect(screen.getByRole("heading", { name: "Por qué este nivel" })).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: "Decisión: local descartado (0.69 < 0.76), economy elegido (0.91 ≥ 0.90)" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Objetivo 0\.90 · router aprendido v1/)).toBeInTheDocument();
    expect(screen.getByText("Figura 1.")).toBeInTheDocument();
    expect(panelText(container)).not.toMatch(/NaN|undefined/);
  });

  it("stops at the local step when p_local clears its threshold", () => {
    render(
      <PlaygroundDecision
        entry={entry({
          final_route_target: "local",
          route_signals: {
            tier: "local",
            p_local: 0.8312,
            p_economy: 0.2,
            quality_target: 0.95,
            operating_point: { tau_local: 0.82, tau_economy: 0.92, quality: 0.957, cost_per_prompt: 0.0017 },
            learned_router: "v1",
          },
        })}
        routeTier="local"
      />,
    );

    expect(screen.getByRole("img", { name: "Decisión: local elegido (0.8312 ≥ 0.82)" })).toBeInTheDocument();
    expect(screen.getByText(/Objetivo 0\.95 · router aprendido v1/)).toBeInTheDocument();
  });

  it("renders an all-frontier operating point as infinite thresholds", () => {
    const { container } = render(
      <PlaygroundDecision
        entry={entry({
          route_signals: {
            tier: "frontier",
            p_local: 0.99,
            p_economy: 0.99,
            quality_target: 1,
            operating_point: { tau_local: null, tau_economy: null, quality: 1, cost_per_prompt: null },
            learned_router: "v1",
          },
        })}
        routeTier="frontier"
      />,
    );

    expect(
      screen.getByRole("img", {
        name: "Decisión: local descartado (0.99 < ∞), economy descartado (0.99 < ∞), frontier elegido",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Objetivo 1\.00 · todo frontier · router aprendido v1/)).toBeInTheDocument();
    expect(panelText(container)).not.toMatch(/NaN|null|undefined/);
  });

  it("says when an economy pick was served by frontier because no economy model is configured", () => {
    render(
      <PlaygroundDecision
        entry={entry({
          route_signals: {
            tier: "frontier",
            p_local: 0.1,
            p_economy: 0.95,
            quality_target: 0.9,
            operating_point: { tau_local: 0.76, tau_economy: 0.9, quality: 0.903, cost_per_prompt: 0.001 },
            learned_router: "v1",
          },
        })}
        routeTier="frontier"
      />,
    );

    expect(screen.getByText(/sin modelo economy configurado/)).toBeInTheDocument();
  });

  it("says the heuristic decided when the embedding was unavailable", () => {
    const { container } = render(
      <PlaygroundDecision
        entry={entry({
          route_reason: "token_complexity",
          final_route_target: "local",
          route_signals: { learned_router: "embedding_unavailable", token_count: 12, complexity_tier: "low" },
        })}
        routeTier=""
      />,
    );

    expect(screen.getByText(/no pudo calcular el embedding/)).toBeInTheDocument();
    expect(screen.getByText(/heurística token_complexity/)).toBeInTheDocument();
    expect(panelText(container)).not.toMatch(/NaN|undefined|p_local/);
  });

  it("says the heuristic decided when the learned router is not active", () => {
    render(
      <PlaygroundDecision
        entry={entry({
          route_reason: "token_complexity",
          route_signals: { token_count: 812, complexity_tier: "high", keyword_match: true },
        })}
        routeTier=""
      />,
    );

    expect(screen.getByText(/Ruteo heurístico \(token_complexity\)/)).toBeInTheDocument();
    expect(screen.getByText(/812 tokens/)).toBeInTheDocument();
  });

  it("explains when no route signals were recorded", () => {
    render(<PlaygroundDecision entry={entry({ route_reason: "token_complexity", route_signals: null })} routeTier="" />);

    expect(screen.getByText(/no registró señales de ruteo/)).toBeInTheDocument();
  });

  it("explains a cache hit as a cache hit even when learned signals are present", () => {
    const { container } = render(
      <PlaygroundDecision
        entry={entry({ route_reason: "cache_hit", final_route_target: "cache",
                       route_signals: { ...entry().route_signals, cache_similarity_score: 0.93 } })}
        routeTier="cache"
      />,
    );
    expect(panelText(container)).toMatch(/caché/);
    expect(panelText(container)).toMatch(/0\.93/);
    expect(panelText(container)).not.toMatch(/embedding/);
  });

  it("explains a local failure fallback on top of the learned decision", () => {
    const { container } = render(
      <PlaygroundDecision entry={entry({ route_reason: "local_provider_error_fallback", fallback_used: true })}
                          routeTier="economy" />,
    );
    expect(panelText(container)).toMatch(/falló el modelo local/i);
    expect(screen.getByRole("img", { name: /local descartado \(0\.69 < 0\.76\)/ })).toBeInTheDocument();
  });

  it("tells a dimension mismatch apart from an unavailable embedding", () => {
    const { container } = render(
      <PlaygroundDecision
        entry={entry({ route_reason: "token_complexity",
                       route_signals: { learned_router: "embedding_dimension_mismatch", token_count: 3 } })}
        routeTier="local"
      />,
    );
    expect(panelText(container)).toMatch(/dimensión/);
  });

  it("does not invent a probability that was not recorded", () => {
    const signals = { ...entry().route_signals } as Record<string, unknown>;
    delete signals.p_local;
    const { container } = render(<PlaygroundDecision entry={entry({ route_signals: signals })} routeTier="economy" />);
    expect(screen.getByRole("img", { name: /local sin dato/ })).toBeInTheDocument();
    expect(panelText(container)).not.toMatch(/p local 0\.00/);
  });
});
