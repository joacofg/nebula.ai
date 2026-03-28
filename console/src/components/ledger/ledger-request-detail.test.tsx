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
};

describe("ledger-request-detail", () => {
  it("renders the persisted explanation fields for a selected embeddings request", () => {
    renderWithProviders(<LedgerRequestDetail entry={mockEntry} />);

    expect(screen.getByText("Request detail")).toBeInTheDocument();
    expect(screen.getByText("Request ID")).toBeInTheDocument();
    expect(screen.getAllByText("req-embed-001")).toHaveLength(2);
    expect(screen.getByText("Tenant")).toBeInTheDocument();
    expect(screen.getByText("tenant-embeddings")).toBeInTheDocument();
    expect(screen.getByText("Route target")).toBeInTheDocument();
    expect(screen.getByText("embeddings")).toBeInTheDocument();
    expect(screen.getByText("Terminal status")).toBeInTheDocument();
    expect(screen.getByText("completed")).toBeInTheDocument();
    expect(screen.getByText("Requested model")).toBeInTheDocument();
    expect(screen.getAllByText("text-embedding-3-small")).toHaveLength(2);
    expect(screen.getByText("Provider")).toBeInTheDocument();
    expect(screen.getByText("openai-compatible")).toBeInTheDocument();
    expect(screen.getByText("Route reason")).toBeInTheDocument();
    expect(screen.getByText("embeddings_request")).toBeInTheDocument();
    expect(screen.getByText("Policy outcome")).toBeInTheDocument();
    expect(screen.getByText("allowed")).toBeInTheDocument();
    expect(screen.getByText("Fallback used")).toBeInTheDocument();
    expect(screen.getByText("Yes")).toBeInTheDocument();
    expect(screen.getByText("Cache hit")).toBeInTheDocument();
    expect(screen.getByText("No")).toBeInTheDocument();
    expect(screen.queryByText(/text to embed/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\[[0-9.,\s-]+\]/)).not.toBeInTheDocument();
  });

  it("shows a neutral empty state when no row is selected", () => {
    renderWithProviders(<LedgerRequestDetail entry={null} />);

    expect(screen.getByText("Select a ledger row to inspect request detail.")).toBeInTheDocument();
  });

  it("falls back to N/A for optional explanation fields that are absent", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          request_id: "req-embed-002",
          final_provider: null,
          fallback_used: false,
          cache_hit: true,
          response_model: null,
          prompt_tokens: 12,
          total_tokens: 12,
          estimated_cost: null,
          latency_ms: null,
          route_reason: null,
          policy_outcome: null,
        }}
      />,
    );

    expect(screen.getByText("Response model")).toBeInTheDocument();
    expect(screen.getAllByText("N/A")).toHaveLength(4);
  });

  it("renders Route Decision section when route_signals is present", () => {
    const entryWithSignals: UsageLedgerRecord = {
      ...mockEntry,
      route_signals: {
        token_count: 842,
        complexity_tier: "medium",
        keyword_match: false,
        model_constraint: false,
        budget_proximity: null,
      },
    };

    renderWithProviders(<LedgerRequestDetail entry={entryWithSignals} />);

    expect(screen.getByText("Route Decision")).toBeInTheDocument();
    expect(screen.getByText("Token count")).toBeInTheDocument();
    expect(screen.getByText("842")).toBeInTheDocument();
    expect(screen.getByText("Complexity tier")).toBeInTheDocument();
    expect(screen.getByText("medium")).toBeInTheDocument();
    expect(screen.getByText("Keyword match")).toBeInTheDocument();
    expect(screen.getByText("Model constraint")).toBeInTheDocument();
    expect(screen.getAllByText("no")).toHaveLength(2);
  });

  it("does not render Route Decision section when route_signals is null", () => {
    renderWithProviders(<LedgerRequestDetail entry={{ ...mockEntry, route_signals: null }} />);

    expect(screen.queryByText("Route Decision")).not.toBeInTheDocument();
  });
});
