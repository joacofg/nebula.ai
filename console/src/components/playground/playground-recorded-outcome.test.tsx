import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PlaygroundRecordedOutcome } from "@/components/playground/playground-recorded-outcome";
import { renderWithProviders } from "@/test/render";

describe("playground-recorded-outcome", () => {
  it("renders the persisted ledger values", () => {
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
        }}
      />,
    );

    expect(screen.getByText("Recorded usage from the Nebula ledger.")).toBeInTheDocument();
    expect(screen.getByText("Terminal status")).toBeInTheDocument();
    expect(screen.getByText("Prompt tokens")).toBeInTheDocument();
    expect(screen.getByText("Completion tokens")).toBeInTheDocument();
    expect(screen.getByText("Total tokens")).toBeInTheDocument();
    expect(screen.getByText("Estimated cost")).toBeInTheDocument();
    expect(screen.getByText("fallback_completed")).toBeInTheDocument();
  });
});
