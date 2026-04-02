import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LedgerRequestDetail } from "@/components/ledger/ledger-request-detail";
import type { CalibrationEvidenceSummary, UsageLedgerRecord } from "@/lib/admin-api";
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

const sufficientCalibration: CalibrationEvidenceSummary = {
  tenant_id: "tenant-embeddings",
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

  it("renders tenant calibration evidence as supporting request context when present", () => {
    renderWithProviders(<LedgerRequestDetail entry={mockEntry} calibrationSummary={sufficientCalibration} />);

    expect(screen.getByText("Calibration evidence")).toBeInTheDocument();
    expect(screen.getByText("Sufficient")).toBeInTheDocument();
    expect(screen.getByText("Tenant evidence is ready for calibrated routing and replay checks.")).toBeInTheDocument();
    expect(
      screen.getByText(/This supports replay readiness and explains the broader routing posture without replacing the persisted story for this request/i),
    ).toBeInTheDocument();
    expect(screen.getByText("Eligible calibrated rows")).toBeInTheDocument();
    expect(screen.getByText("7 of 5 needed")).toBeInTheDocument();
    expect(screen.getByText("Degraded rows")).toBeInTheDocument();
    expect(screen.getByText(/Missing Route Signals \(1\)/i)).toBeInTheDocument();
  });

  it("renders rollout-disabled calibration messaging when traffic is gated by operator rollout state", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={mockEntry}
        calibrationSummary={{
          ...sufficientCalibration,
          state: "thin",
          state_reason: "Calibrated routing remained disabled for recent tenant traffic.",
          eligible_request_count: 0,
          sufficient_request_count: 0,
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

    expect(screen.getByText("Rollout disabled")).toBeInTheDocument();
    expect(screen.getByText("Tenant traffic is visible, but calibrated routing rollout is still operator-gated.")).toBeInTheDocument();
    expect(screen.getByText("Rollout-disabled rows")).toBeInTheDocument();
    expect(screen.getByText(/Calibrated Routing Disabled \(3\)/i)).toBeInTheDocument();
  });

  it("renders stale calibration messaging when evidence is old", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={mockEntry}
        calibrationSummary={{
          ...sufficientCalibration,
          state: "stale",
          state_reason: "Eligible calibrated evidence exists but is older than the freshness window.",
        }}
      />,
    );

    expect(screen.getByText("Stale")).toBeInTheDocument();
    expect(screen.getByText("Tenant evidence exists, but the eligible calibrated window is stale.")).toBeInTheDocument();
    expect(screen.getByText("Staleness threshold")).toBeInTheDocument();
    expect(screen.getByText("24 hours")).toBeInTheDocument();
  });

  it("renders structured hard-budget downgrade evidence instead of forcing raw policy_outcome inspection", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          request_id: "req-budget-downgrade",
          final_route_target: "local",
          route_reason: "hard_budget_downgrade",
          policy_outcome:
            "hard_budget=exceeded(limit_usd=0.05,spent_usd=0.1,enforcement=downgrade);budget_action=downgraded_to_local",
        }}
      />,
    );

    expect(screen.getByText("Budget policy evidence")).toBeInTheDocument();
    expect(screen.getByText("Premium traffic downgraded to local")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Cumulative premium spend hit the tenant hard budget, so this request stayed allowed by routing to a local model instead of premium.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Budget action")).toBeInTheDocument();
    expect(screen.getByText("Downgraded to local")).toBeInTheDocument();
    expect(screen.getByText("Hard budget limit")).toBeInTheDocument();
    expect(screen.getByText("$0.05")).toBeInTheDocument();
    expect(screen.getByText("Spent at decision")).toBeInTheDocument();
    expect(screen.getByText("$0.1")).toBeInTheDocument();
    expect(screen.getByText("Hard budget enforcement")).toBeInTheDocument();
    expect(screen.getByText("Downgrade")).toBeInTheDocument();
  });

  it("renders structured hard-budget denial evidence from persisted ledger policy outcomes", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          request_id: "req-budget-denied",
          final_route_target: "denied",
          terminal_status: "policy_denied",
          policy_outcome:
            "Tenant hard budget limit reached; premium routing is blocked (spent_usd=0.1, limit_usd=0.05).",
        }}
      />,
    );

    expect(screen.getByText("Budget policy evidence")).toBeInTheDocument();
    expect(screen.getByText("Premium request denied by budget guardrail")).toBeInTheDocument();
    expect(
      screen.getAllByText(
        "Tenant hard budget limit reached; premium routing is blocked (spent_usd=0.1, limit_usd=0.05).",
      ).length,
    ).toBeGreaterThan(1);
    expect(screen.getByText("Denial reason")).toBeInTheDocument();
    expect(screen.getByText("Hard budget limit")).toBeInTheDocument();
    expect(screen.getByText("Spent at decision")).toBeInTheDocument();
  });

  it("renders soft-budget advisory evidence as non-blocking operator guidance", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          request_id: "req-soft-budget",
          policy_outcome: "soft_budget=exceeded",
        }}
      />,
    );

    expect(screen.getByText("Budget policy evidence")).toBeInTheDocument();
    expect(screen.getByText("Soft budget advisory triggered")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Cumulative spend exceeded the advisory soft budget. Routing continued, but the request was tagged for operator visibility.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Soft budget status")).toBeInTheDocument();
    expect(screen.getByText("Exceeded (advisory only)")).toBeInTheDocument();
  });

  it("does not render calibration evidence when no tenant summary is available", () => {
    renderWithProviders(<LedgerRequestDetail entry={mockEntry} calibrationSummary={null} />);

    expect(screen.queryByText("Calibration evidence")).not.toBeInTheDocument();
  });

  it("does not render Route Decision section when route_signals is null", () => {
    renderWithProviders(<LedgerRequestDetail entry={{ ...mockEntry, route_signals: null }} />);

    expect(screen.queryByText("Route Decision")).not.toBeInTheDocument();
  });
});
