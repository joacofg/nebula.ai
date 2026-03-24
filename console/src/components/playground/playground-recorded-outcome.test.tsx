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
        }}
      />,
    );

    expect(screen.getByRole("heading", { name: "Recorded outcome" })).toBeInTheDocument();
    expect(
      screen.getByText(
        "Persisted ledger evidence for the same request after Nebula records the final route, provider, fallback, and policy outcome.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Terminal status")).toBeInTheDocument();
    expect(screen.getByText("Route target")).toBeInTheDocument();
    expect(screen.getByText("Provider")).toBeInTheDocument();
    expect(screen.getByText("Route reason")).toBeInTheDocument();
    expect(screen.getByText("Policy outcome")).toBeInTheDocument();
    expect(screen.getByText("Fallback used")).toBeInTheDocument();
    expect(screen.getByText("Cache hit")).toBeInTheDocument();
    expect(screen.getByText("Prompt tokens")).toBeInTheDocument();
    expect(screen.getByText("Completion tokens")).toBeInTheDocument();
    expect(screen.getByText("Total tokens")).toBeInTheDocument();
    expect(screen.getByText("Estimated cost")).toBeInTheDocument();
    expect(screen.getByText("fallback_completed")).toBeInTheDocument();
    expect(screen.getByText("premium")).toBeInTheDocument();
    expect(screen.getByText("openai-compatible")).toBeInTheDocument();
    expect(screen.getByText("fallback")).toBeInTheDocument();
    expect(screen.getByText("allowed")).toBeInTheDocument();
    expect(screen.getByText("21")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("33")).toBeInTheDocument();
    expect(screen.getByText("Yes")).toBeInTheDocument();
    expect(screen.getByText("No")).toBeInTheDocument();
    expect(screen.getByText("$0.0180")).toBeInTheDocument();
  });
});
