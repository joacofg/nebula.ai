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
    expect(
      screen.getByText(
        "This persisted ledger record is the authoritative evidence row for this request ID while the row still exists.",
        { exact: false },
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/before reading broader tenant or hosted posture guidance elsewhere on this page/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /If governed retention cleanup later deletes the row at its persisted expiration time, this request detail should disappear with it/i,
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/rather than imply recovery, a soft-deleted archive, or hosted raw export/i)).toBeInTheDocument();
    expect(screen.getByText("Effective evidence boundary")).toBeInTheDocument();
    expect(screen.getByText("Row-level governance truth")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Retained request detail stays local to the persisted ledger row while that governed row still exists.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Suppressed means governance removed or never wrote specific metadata fields, so those fields are no longer available from the ledger later.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Deleted means governed retention removed the entire row at expiration; Nebula should not imply recovery, soft-delete archives, or hidden raw exports afterward.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Not hosted means the hosted control plane does not receive raw usage-ledger rows and cannot replace the local row as request-level evidence.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Hosted export still excludes raw usage-ledger rows; operators must confirm serving-time behavior from local runtime surfaces.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/dashboard/i)).not.toBeInTheDocument();
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
          metadata_fields_suppressed: undefined as unknown as string[],
        }}
      />,
    );

    expect(screen.getByText("Response model")).toBeInTheDocument();
    expect(screen.getAllByText("N/A")).toHaveLength(4);
    expect(screen.getByText("Suppressed metadata fields")).toBeInTheDocument();
    expect(screen.getByText("None")).toBeInTheDocument();
  });

  it("renders grounded routing inspection with additive score components", () => {
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
    expect(screen.getAllByText("grounded (score 1.00)")).toHaveLength(2);
    expect(
      screen.getByText(
        "This selected request used grounded routing from the full calibrated signal set recorded on the persisted row, including the additive score breakdown when present.",
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

    expect(screen.getAllByText("degraded (score 0.60)")).toHaveLength(2);
    expect(
      screen.getByText(
        "This selected request used degraded routing because replay-critical calibrated inputs were incomplete on the persisted row. Treat any tenant summary as supporting context only.",
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
        "This selected request shows rollout disabled at the row level, so operators can distinguish intentional gating from missing routing data without relying on tenant-level summaries.",
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
        "This selected request did not carry a grounded or degraded score path. That is explicit row-level evidence, not a generic analytics gap or missing tenant summary.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText("Route mode")).not.toBeInTheDocument();
    expect(screen.queryByText("Route score")).not.toBeInTheDocument();
  });

  it("renders tenant calibration evidence as supporting request context when present", () => {
    renderWithProviders(<LedgerRequestDetail entry={mockEntry} calibrationSummary={sufficientCalibration} />);

    expect(screen.getByText("Calibration evidence")).toBeInTheDocument();
    expect(screen.getByText("Grounded")).toBeInTheDocument();
    expect(screen.getByText("Tenant evidence is grounded enough to support calibrated routing and replay checks.")).toBeInTheDocument();
    expect(
      screen.getByText(/Use that tenant summary only as supporting context for this selected request, whose persisted row remains the authoritative proof surface/i),
    ).toBeInTheDocument();
    expect(screen.getByText("Eligible grounded rows")).toBeInTheDocument();
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

  it("renders degraded calibration messaging when supporting evidence is partial", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={mockEntry}
        calibrationSummary={{
          ...sufficientCalibration,
          state: "degraded",
          state_reason: "Recent eligible traffic degraded because calibrated factors were incomplete.",
          eligible_request_count: 2,
          sufficient_request_count: 2,
          degraded_request_count: 4,
          degraded_reasons: [{ reason: "missing_route_signals", count: 4 }],
          excluded_request_count: 0,
          excluded_reasons: [],
          gated_request_count: 0,
          gated_reasons: [],
        }}
      />,
    );

    expect(screen.getByText("Degraded")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Tenant evidence is degraded, so supporting context stays partial for calibrated routing review.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Recent traffic produced degraded evidence instead of a fully grounded window. Keep the selected request row authoritative and treat this tenant summary as a partial explanation of why broader calibrated evidence is limited.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Eligible grounded rows")).toBeInTheDocument();
    expect(screen.getByText("2 of 5 needed")).toBeInTheDocument();
    expect(screen.getByText("Degraded rows")).toBeInTheDocument();
    expect(screen.getByText(/Missing Route Signals \(4\)/i)).toBeInTheDocument();
  });

  it("keeps degraded row-level routing authoritative over supporting tenant summaries", () => {
    renderWithProviders(
      <LedgerRequestDetail
        entry={{
          ...mockEntry,
          request_id: "req-degraded-authoritative",
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
        calibrationSummary={{
          ...sufficientCalibration,
          state: "degraded",
          state_reason: "Recent eligible traffic degraded because calibrated factors were incomplete.",
          eligible_request_count: 2,
          sufficient_request_count: 2,
          degraded_request_count: 4,
          degraded_reasons: [{ reason: "missing_route_signals", count: 4 }],
          excluded_request_count: 0,
          excluded_reasons: [],
          gated_request_count: 0,
          gated_reasons: [],
        }}
      />,
    );

    const detailText = screen.getByText(
      "This selected request used degraded routing because replay-critical calibrated inputs were incomplete on the persisted row. Treat any tenant summary as supporting context only.",
    );
    const calibrationText = screen.getByText(
      "Recent traffic produced degraded evidence instead of a fully grounded window. Keep the selected request row authoritative and treat this tenant summary as a partial explanation of why broader calibrated evidence is limited.",
    );

    expect(screen.getAllByText("degraded (score 0.60)")).toHaveLength(2);
    expect(screen.getByText("Calibration evidence")).toBeInTheDocument();
    expect(screen.getByText("Degraded")).toBeInTheDocument();
    expect(screen.getByText(/Missing Route Signals \(4\)/i)).toBeInTheDocument();

    const pageText = screen.getByText("Request detail").closest("section")?.textContent ?? "";
    expect(pageText.indexOf("Request detail")).toBeGreaterThanOrEqual(0);
    expect(pageText.indexOf("Calibration evidence")).toBeGreaterThan(pageText.indexOf("Request detail"));
    expect(pageText.indexOf("Routing inspection")).toBeGreaterThan(pageText.indexOf("Request detail"));
    expect(pageText).toContain("Treat any tenant summary as supporting context only.");
    expect(pageText).toContain("Keep the selected request row authoritative");
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
