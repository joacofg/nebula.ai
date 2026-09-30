import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PlaygroundRecordedOutcome } from "@/components/playground/playground-recorded-outcome";
import { renderWithProviders } from "@/test/render";

describe("playground-recorded-outcome", () => {
  it("renders the persisted ledger route, provider, fallback, policy, and cost evidence", () => {
    renderWithProviders(
      <PlaygroundRecordedOutcome
        entry={{
          request_id: "req-123",
          tenant_id: "default",
          requested_model: "openai/gpt-4o-mini",
          final_route_target: "premium",
          final_provider: "openai-compatible",
          fallback_used: true,
          cache_hit: false,
          response_model: "openai/gpt-4o-mini",
          prompt_tokens: 21,
          completion_tokens: 12,
          total_tokens: 33,
          estimated_cost: 0.018,
          latency_ms: 201,
          timestamp: "2026-03-16T22:00:00Z",
          terminal_status: "fallback_completed",
          route_reason: "fallback",
          policy_outcome: "allowed",
          route_signals: null,
          message_type: "chat",
          evidence_retention_window: "30d",
          evidence_expires_at: null,
          metadata_minimization_level: "standard",
          metadata_fields_suppressed: [],
          governance_source: "tenant_policy",
        }}
      />,
    );

    expect(screen.getByRole("heading", { name: "Registro en el ledger" })).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Estado" })).toHaveTextContent("fallback_completed");
    expect(screen.getByRole("group", { name: "Ruta" })).toHaveTextContent("premium");
    expect(screen.getByRole("group", { name: "Proveedor" })).toHaveTextContent("openai-compatible");
    expect(screen.getByRole("group", { name: "Motivo" })).toHaveTextContent("fallback");
    expect(screen.getByRole("group", { name: "Política" })).toHaveTextContent("allowed");
    expect(screen.getByRole("group", { name: "Tokens" })).toHaveTextContent("21 + 12 = 33");
    expect(screen.getByRole("group", { name: "Fallback" })).toHaveTextContent("sí");
    expect(screen.getByRole("group", { name: "Caché" })).toHaveTextContent("no");
    expect(screen.getByRole("group", { name: "Costo estimado" })).toHaveTextContent("USD 0.0180");
  });
});
