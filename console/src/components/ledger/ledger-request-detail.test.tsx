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
  message_type: "embeddings",
  evidence_retention_window: "30d",
  evidence_expires_at: "2026-04-16T01:02:03Z",
  metadata_minimization_level: "strict",
  metadata_fields_suppressed: [],
  governance_source: "tenant_policy",
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
    expect(screen.getByText("This persisted ledger record is the authoritative evidence row for this request ID.", { exact: false })).toBeInTheDocument();
    expect(screen.getByText(/before reading the supporting tenant context elsewhere on this page/i)).toBeInTheDocument();
    expect(screen.getByText("Request ID")).toBeInTheDocument();
    expect(screen.getAllByText("req-embed-001")).toHaveLength(2);
    expect(screen.getByText("Tenant")).toBeInTheDocument();
    expect(screen.getByText("tenant-embeddings")).toBeInTheDocument();
    expect(screen.getByText("Message type")).toBeInTheDocument();
    expect(screen.getByText("Route target")).toBeInTheDocument();
    expect(screen.getAllByText("embeddings").length).toBeGreaterThanOrEqual(2);
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
    expect(screen.getByText("Evidence retention")).toBeInTheDocument();
    expect(screen.getByText("30d")).toBeInTheDocument();
    expect(screen.getByText("Evidence expires at")).toBeInTheDocument();
    expect(screen.getByText("Metadata minimization")).toBeInTheDocument();
    expect(screen.getByText("strict")).toBeInTheDocument();
    expect(screen.getByText("Suppressed metadata fields")).toBeInTheDocument();
    expect(screen.getByText("Governance source")).toBeInTheDocument();
    expect(screen.getByText("tenant_policy")).toBeInTheDocument();
    expect(screen.getByText("Fallback used")).toBeInTheDocument();
    expect(screen.getByText("Yes")).toBeInTheDocument();
    expect(screen.getByText("Cache hit")).toBeInTheDocument();
    expect(screen.getByText("No")).toBeInTheDocument();
    expect(screen.queryByText(/text to embed/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\[[0-9.,\s-]+\]/)).not.toBeInTheDocument();
    expect(screen.queryByText(/dashboard/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/routing studio/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/analytics product/i)).not.toBeInTheDocument();
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

  it("renders calibrated routing inspection with additive score components", () => {
    const entryWithSignals: UsageLedgerRecord = {
      ...mockEntry,
      route_reason: "token_complexity",
      route_signals: {
        token_count: 842,
        complexity_tier: "medium",
        keyword_match: true,
        model_constraint: true,
        budget_proximity: null,
        route_mode: "calibrated",
        calibrated_routing: true,
        degraded_routing: false,
        score_components: {
          token_score: 1,
          keyword_bonus: 0.2,
          policy_bonus: 0.1,
          budget_penalty: 0,
          total_score: 1,
        },
      },
    };

    renderWithProviders(<LedgerRequestDetail entry={entryWithSignals} />);

    expect(screen.getByText("Routing inspection")).toBeInTheDocument();
    expect(screen.getAllByText("calibrated (calibrated, score 1.00)")).toHaveLength(2);
    expect(
      screen.getByText(
        "Routing used the full calibrated signal set recorded for this request, including the additive score breakdown when present.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Route mode")).toBeInTheDocument();
    expect(screen.getByText("calibrated")).toBeInTheDocument();
    expect(screen.getByText("Route score")).toBeInTheDocument();
    expect(screen.getAllByText("1.00").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("Token score")).toBeInTheDocument();
    expect(screen.getByText("Keyword bonus")).toBeInTheDocument();
    expect(screen.getByText("Policy bonus")).toBeInTheDocument();
    expect(screen.getByText("Budget penalty")).toBeInTheDocument();
    expect(screen.getByText("Route signals")).toBeInTheDocument();
    expect(screen.getByText("Token count")).toBeInTheDocument();
    expect(screen.getByText("842")).toBeInTheDocument();
    expect(screen.getByText("Complexity tier")).toBeInTheDocument();
    expect(screen.getByText("medium")).toBeInTheDocument();
  });

  it("renders degraded routing inspection when replay-critical signals were incomplete", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          request_id: "req-degraded",
          route_reason: "token_complexity",
          route_signals: {
            token_count: 300,
            complexity_tier: "low",
            keyword_match: false,
            model_constraint: false,
            route_mode: "degraded",
            calibrated_routing: false,
            degraded_routing: true,
            score_components: {
              token_score: 0.6,
              keyword_bonus: 0,
              policy_bonus: 0,
              budget_penalty: 0,
              total_score: 0.6,
            },
          },
        }}
      />,
    );

    expect(screen.getAllByText("degraded (degraded, score 0.60)")).toHaveLength(2);
    expect(
      screen.getByText(
        "Routing fell back to degraded scoring because replay-critical calibrated inputs were incomplete for this persisted row.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Route mode")).toBeInTheDocument();
    expect(screen.getByText("degraded")).toBeInTheDocument();
    expect(screen.getByText("Route score")).toBeInTheDocument();
    expect(screen.getAllByText("0.60").length).toBeGreaterThanOrEqual(2);
  });

  it("keeps rollout-disabled null-mode rows explicit instead of treating them as missing data", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          request_id: "req-rollout-disabled",
          route_reason: "calibrated_routing_disabled",
          route_signals: {
            token_count: 144,
            complexity_tier: "low",
            keyword_match: false,
            model_constraint: false,
          },
        }}
      />,
    );

    expect(screen.getAllByText("rollout disabled")).toHaveLength(2);
    expect(
      screen.getByText(
        "Calibrated routing was intentionally disabled for this request, so the row stays explicit about rollout state instead of looking like missing routing data.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText("Route mode")).not.toBeInTheDocument();
    expect(screen.queryByText("Route score")).not.toBeInTheDocument();
  });

  it("renders unscored inspection when signals are partial but no calibrated score participated", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          request_id: "req-unscored",
          route_reason: "explicit_premium_model",
          route_signals: {
            token_count: 61,
            complexity_tier: "low",
            keyword_match: false,
          },
        }}
      />,
    );

    expect(screen.getAllByText("unscored")).toHaveLength(2);
    expect(
      screen.getByText(
        "This row did not carry a calibrated score path. That is explicit request-level state, not a generic analytics gap.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText("Route mode")).not.toBeInTheDocument();
    expect(screen.queryByText("Route score")).not.toBeInTheDocument();
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
    expect(screen.queryByText(/authoritative evidence row/i)).not.toHaveTextContent;
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

  it("does not render routing sections when route_signals is null", () => {
    renderWithProviders(<LedgerRequestDetail entry={{ ...mockEntry, route_signals: null }} />);

    expect(screen.queryByText("Routing inspection")).not.toBeInTheDocument();
    expect(screen.queryByText("Route signals")).not.toBeInTheDocument();
  });
});
