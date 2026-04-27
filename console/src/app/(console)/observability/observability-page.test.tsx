import { render, screen, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ObservabilityPage from "./page";

const listTenants = vi.fn();
const listUsageLedger = vi.fn();
const getTenantRecommendations = vi.fn();

vi.mock("@/lib/admin-api", () => ({
  listTenants: (...args: unknown[]) => listTenants(...args),
  listUsageLedger: (...args: unknown[]) => listUsageLedger(...args),
  getTenantRecommendations: (...args: unknown[]) => getTenantRecommendations(...args),
}));

vi.mock("@/lib/admin-session-provider", () => ({
  useAdminSession: () => ({ adminKey: "nebula-admin-key" }),
}));

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ObservabilityPage />
    </QueryClientProvider>,
  );
}

function getTopLevelSectionHeadings(container: HTMLElement) {
  return Array.from(container.querySelectorAll(":scope > section > header h2")).map((heading) =>
    heading.textContent?.trim() ?? "",
  );
}

function expectHeadingOrder(container: HTMLElement, expectedOrder: string[]) {
  expect(getTopLevelSectionHeadings(container)).toEqual(expectedOrder);
}

function expectTextToAppearBefore(container: HTMLElement, first: string, second: string) {
  const content = container.textContent ?? "";
  const firstIndex = content.indexOf(first);
  const secondIndex = content.indexOf(second);

  expect(firstIndex).toBeGreaterThanOrEqual(0);
  expect(secondIndex).toBeGreaterThanOrEqual(0);
  expect(firstIndex).toBeLessThan(secondIndex);
}

describe("ObservabilityPage", () => {
  beforeEach(() => {
    listTenants.mockResolvedValue([{ id: "tenant-alpha", name: "Tenant Alpha" }]);
    listUsageLedger.mockResolvedValue([
      {
        request_id: "req-integrated-001",
        tenant_id: "tenant-alpha",
        requested_model: "gpt-4o-mini",
        final_route_target: "premium",
        final_provider: "openai-compatible",
        fallback_used: false,
        cache_hit: false,
        response_model: "gpt-4o-mini",
        prompt_tokens: 12,
        completion_tokens: 18,
        total_tokens: 30,
        estimated_cost: 0.0042,
        latency_ms: 210,
        timestamp: "2026-03-23T18:00:00Z",
        terminal_status: "completed",
        route_reason: "complexity_high",
        policy_outcome: "allowed",
        route_signals: {
          route_mode: "calibrated",
          calibrated_routing: true,
          degraded_routing: false,
          route_score: 0.91,
          token_count: 30,
          complexity_tier: "high",
          keyword_match: true,
          model_constraint: false,
          budget_proximity: 0.33,
          score_components: {
            total_score: 0.91,
            token_score: 0.66,
            keyword_bonus: 0.15,
            policy_bonus: 0.1,
            budget_penalty: 0,
          },
        },
        message_type: "chat",
        evidence_retention_window: "30d",
        evidence_expires_at: "2026-04-22T18:00:00Z",
        metadata_minimization_level: "standard",
        metadata_fields_suppressed: ["request_body", "response_body"],
        governance_source: "tenant_policy",
      },
    ]);
    getTenantRecommendations.mockResolvedValue({
      tenant_id: "tenant-alpha",
      generated_at: "2026-03-27T18:00:00Z",
      window_requests_evaluated: 30,
      calibration_summary: {
        tenant_id: "tenant-alpha",
        scope: "tenant",
        state: "sufficient",
        state_reason: "Recent eligible calibrated rows meet the tenant sufficiency threshold.",
        generated_at: "2026-03-27T18:00:00Z",
        latest_eligible_request_at: "2026-03-27T17:15:00Z",
        latest_any_request_at: "2026-03-27T17:15:00Z",
        eligible_request_count: 12,
        sufficient_request_count: 12,
        thin_request_threshold: 5,
        staleness_threshold_hours: 24,
        excluded_request_count: 1,
        gated_request_count: 0,
        degraded_request_count: 1,
        excluded_reasons: [{ reason: "policy_forced_route", count: 1 }],
        gated_reasons: [],
        degraded_reasons: [{ reason: "missing_route_signals", count: 1 }],
      },
      recommendations: [
        {
          code: "cache-window-review",
          title: "Review cache aging window",
          priority: 2,
          category: "cache",
          summary: "Recent ledger-backed traffic suggests useful reuse, but long entry age may widen stale-response risk.",
          recommended_action: "Preview a lower max entry age in policy before saving any runtime change.",
          evidence: [
            { label: "Requests evaluated", value: "30" },
            { label: "Current max age", value: "168 hours" },
          ],
        },
      ],
      cache_summary: {
        enabled: true,
        similarity_threshold: 0.9,
        max_entry_age_hours: 168,
        runtime_status: "degraded",
        runtime_detail: "Qdrant is warming and may reduce cache consistency.",
        estimated_hit_rate: 0.38,
        avoided_premium_cost_usd: 0.84,
        insights: [
          {
            code: "cache-runtime-degraded",
            title: "Degraded cache runtime remains visible",
            level: "notice",
            summary: "Cache lookups still return value, but degraded runtime should be part of the operator explanation.",
            evidence: [{ label: "Runtime status", value: "degraded" }],
          },
        ],
      },
    });

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          dependencies: {
            postgres: { status: "healthy", required: true, detail: "ready" },
            qdrant: { status: "degraded", required: false, detail: "warming" },
          },
        }),
      }),
    );
  });

  it("renders request-first observability framing with bounded supporting context", async () => {
    const { container } = renderPage();

    expect(await screen.findByRole("heading", { name: "Selected request evidence first" })).toBeInTheDocument();
    expect(screen.getByText(/Start with one persisted ledger row for the selected request ID/i)).toBeInTheDocument();
    expect(screen.getByText(/Calibration readiness, grounded recommendations, cache posture, and dependency health stay on this page as supporting runtime context/i)).toBeInTheDocument();

    expectHeadingOrder(container.firstElementChild as HTMLElement, [
      "Inspect one persisted ledger row before reading tenant context",
      "Follow-up context for the selected request",
    ]);
    expectTextToAppearBefore(
      container.firstElementChild as HTMLElement,
      "Inspect one persisted ledger row before reading tenant context",
      "Follow-up context for the selected request",
    );
    expect(screen.queryByText(/dashboard/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/routing studio/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/analytics/i)).not.toBeInTheDocument();

    const selectedRequestSection = screen
      .getByRole("heading", { name: "Inspect one persisted ledger row before reading tenant context" })
      .closest("section");
    expect(selectedRequestSection).not.toBeNull();
    const selectedRequest = within(selectedRequestSection!);
    expect(selectedRequest.getByText(/Pick the request first\./i)).toBeInTheDocument();
    expect(selectedRequest.getByText(/The selected ledger row remains the authoritative persisted record/i)).toBeInTheDocument();
    expect(selectedRequest.getByText(/they do not overrule the selected request evidence/i)).toBeInTheDocument();

    const followUpSection = screen.getByRole("heading", { name: "Follow-up context for the selected request" }).closest("section");
    expect(followUpSection).not.toBeNull();
    expect(selectedRequestSection!.compareDocumentPosition(followUpSection!)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);

    await screen.findByText("Request detail");
    const requestDetailSection = within(selectedRequestSection!);
    expect((await requestDetailSection.findAllByText("req-integrated-001")).length).toBeGreaterThanOrEqual(2);
    expect(requestDetailSection.getByText("Request detail")).toBeInTheDocument();
    expect(requestDetailSection.getAllByText("req-integrated-001").length).toBeGreaterThanOrEqual(2);
    expect(requestDetailSection.getByText("Calibration evidence")).toBeInTheDocument();
    expect(
      requestDetailSection.getByText("Tenant evidence is grounded enough to support calibrated routing and replay checks."),
    ).toBeInTheDocument();
    expect(requestDetailSection.getByText("Grounded")).toBeInTheDocument();
    expect(requestDetailSection.getByText("Routing inspection")).toBeInTheDocument();
    expect(requestDetailSection.getAllByText("grounded (score 0.91)")).toHaveLength(2);
    expect(requestDetailSection.getByText("Suppressed metadata fields")).toBeInTheDocument();
    expect(requestDetailSection.getByText("Request Body, Response Body")).toBeInTheDocument();
    expect(requestDetailSection.getByText("Recent eligible calibrated rows meet the tenant sufficiency threshold.")).toBeInTheDocument();

    const selectedRequestText = selectedRequestSection!.textContent ?? "";
    const followUpText = followUpSection!.textContent ?? "";
    expect(selectedRequestText.indexOf("req-integrated-001")).toBeGreaterThanOrEqual(0);
    expect(selectedRequestText.indexOf("Routing inspection")).toBeGreaterThanOrEqual(0);
    expect(followUpText.indexOf("Review cache aging window")).toBeGreaterThanOrEqual(0);
    expect(followUpText.indexOf("Dependency health context")).toBeGreaterThanOrEqual(0);
    expect(selectedRequestText.indexOf("req-integrated-001")).toBeLessThan(
      (container.firstElementChild?.textContent ?? "").indexOf("Dependency health context"),
    );

    const followUp = within(followUpSection!);
    expect(followUp.getByText(/use these supporting cards to decide the next operator action/i)).toBeInTheDocument();
    expect(followUp.getByText(/point toward policy preview as the comparison surface before any save elsewhere in the console/i)).toBeInTheDocument();

    const guidanceCard = followUp
      .getByRole("heading", { name: "Grounded follow-up guidance for the selected request" })
      .closest("article");
    expect(guidanceCard).not.toBeNull();
    const guidance = within(guidanceCard!);
    expect(guidance.getByText(/bounded operator guidance for the selected-request investigation/i)).toBeInTheDocument();
    expect(guidance.getByText(/Compare options in policy preview before saving any change elsewhere in the console/i)).toBeInTheDocument();

    const policyPreviewCard = followUp.getByRole("heading", { name: "Policy preview follow-up for the same request" }).closest("article");
    expect(policyPreviewCard).not.toBeNull();
    const policyPreview = within(policyPreviewCard!);
    expect(policyPreview.getByText(/Use calibration, cache, and dependency context to judge whether a policy preview comparison is grounded enough/i)).toBeInTheDocument();
    expect(policyPreview.getByText(/This page stays inspection-only: preview before saving in the policy editor/i)).toBeInTheDocument();
    expect(policyPreview.getByText(/keep the persisted request row as the authoritative evidence seam/i)).toBeInTheDocument();

    const replayReadinessHeading = await screen.findByRole("heading", { name: "Tenant-scoped replay readiness context" });
    const replayReadinessCard = replayReadinessHeading.closest("article");
    expect(replayReadinessCard).not.toBeNull();
    const replayReadiness = within(replayReadinessCard!);
    expect(replayReadiness.getByText(/derived from existing ledger metadata for the selected tenant/i)).toBeInTheDocument();
    expect(replayReadiness.getByText(/without turning Observability into a replacement for the persisted request record/i)).toBeInTheDocument();
    expect(replayReadiness.getByText(/before deciding whether a replay or policy preview comparison is grounded enough/i)).toBeInTheDocument();
    expect(replayReadiness.getByText("Eligible calibrated rows")).toBeInTheDocument();
    expect(replayReadiness.getByText("12")).toBeInTheDocument();
    expect(replayReadiness.getByText("Sufficiency threshold")).toBeInTheDocument();
    expect(replayReadiness.getByText("5")).toBeInTheDocument();
    expect(replayReadiness.getByText(/Keep using the ledger row and request ID correlation as the primary proof\./i)).toBeInTheDocument();

    expect(screen.getAllByText("Recent eligible calibrated rows meet the tenant sufficiency threshold.")).toHaveLength(2);
    expect(await followUp.findByText("Review cache aging window")).toBeInTheDocument();
    expect(followUp.getByText(/Preview a lower max entry age in policy before saving any runtime change/i)).toBeInTheDocument();

    const cacheCard = followUp.getByRole("heading", { name: "Cache effectiveness and runtime controls" }).closest("section");
    expect(cacheCard).not.toBeNull();
    const cache = within(cacheCard!);
    expect(cache.getByText(/Use it to decide whether the next step is a policy preview comparison/i)).toBeInTheDocument();
    expect(cache.getByText("Runtime detail:")).toBeInTheDocument();
    expect(cache.getByText(/Qdrant is warming and may reduce cache consistency/i)).toBeInTheDocument();
    expect(cache.getByText("Similarity threshold")).toBeInTheDocument();
    expect(cache.getByText("0.90")).toBeInTheDocument();
    expect(cache.getByText("Max entry age")).toBeInTheDocument();
    expect(cache.getByText("168 hours")).toBeInTheDocument();

    const dependencySection = followUp.getByRole("heading", { name: "Dependency health context" }).closest("section");
    expect(dependencySection).not.toBeNull();
    const dependency = within(dependencySection!);
    expect(dependency.getByText(/Required dependency failures block confidence immediately/i)).toBeInTheDocument();
    expect(await screen.findAllByText("tenant-alpha")).toHaveLength(2);
    expect(await screen.findAllByText("Route target")).toHaveLength(3);
  });

  it("renders thin calibration evidence without inventing a separate analytics flow", async () => {
    getTenantRecommendations.mockResolvedValueOnce({
      tenant_id: "tenant-alpha",
      generated_at: "2026-03-27T18:00:00Z",
      window_requests_evaluated: 3,
      calibration_summary: {
        tenant_id: "tenant-alpha",
        scope: "tenant",
        state: "thin",
        state_reason: "Eligible calibrated routing evidence is still below the tenant sufficiency threshold.",
        generated_at: "2026-03-27T18:00:00Z",
        latest_eligible_request_at: "2026-03-27T16:00:00Z",
        latest_any_request_at: "2026-03-27T16:30:00Z",
        eligible_request_count: 3,
        sufficient_request_count: 3,
        thin_request_threshold: 5,
        staleness_threshold_hours: 24,
        excluded_request_count: 0,
        gated_request_count: 0,
        degraded_request_count: 0,
        excluded_reasons: [],
        gated_reasons: [],
        degraded_reasons: [],
      },
      recommendations: [],
      cache_summary: {
        enabled: true,
        similarity_threshold: 0.9,
        max_entry_age_hours: 168,
        runtime_status: "ready",
        runtime_detail: "Ready",
        estimated_hit_rate: 0.1,
        avoided_premium_cost_usd: 0.02,
        insights: [],
      },
    });

    renderPage();

    expect(await screen.findByText("thin")).toBeInTheDocument();
    expect(screen.getAllByText("Eligible calibrated routing evidence is still below the tenant sufficiency threshold.")).toHaveLength(2);
    expect(screen.getByText(/Keep using the ledger row and request ID correlation as the primary proof/i)).toBeInTheDocument();
    expect(screen.queryByText(/analytics/i)).not.toBeInTheDocument();
  });

  it("renders stale calibration evidence when the tenant window is no longer fresh", async () => {
    getTenantRecommendations.mockResolvedValueOnce({
      tenant_id: "tenant-alpha",
      generated_at: "2026-03-27T18:00:00Z",
      window_requests_evaluated: 11,
      calibration_summary: {
        tenant_id: "tenant-alpha",
        scope: "tenant",
        state: "stale",
        state_reason: "Eligible calibrated evidence exists but the newest row is outside the freshness window.",
        generated_at: "2026-03-27T18:00:00Z",
        latest_eligible_request_at: "2026-03-24T12:00:00Z",
        latest_any_request_at: "2026-03-27T17:00:00Z",
        eligible_request_count: 11,
        sufficient_request_count: 11,
        thin_request_threshold: 5,
        staleness_threshold_hours: 24,
        excluded_request_count: 0,
        gated_request_count: 0,
        degraded_request_count: 1,
        excluded_reasons: [],
        gated_reasons: [],
        degraded_reasons: [{ reason: "missing_route_signals", count: 1 }],
      },
      recommendations: [],
      cache_summary: {
        enabled: false,
        similarity_threshold: 0.9,
        max_entry_age_hours: 168,
        runtime_status: "unknown",
        runtime_detail: "Unavailable",
        estimated_hit_rate: 0,
        avoided_premium_cost_usd: 0,
        insights: [],
      },
    });

    renderPage();

    expect(await screen.findByText("stale")).toBeInTheDocument();
    expect(screen.getAllByText("Eligible calibrated evidence exists but the newest row is outside the freshness window.")).toHaveLength(2);
  });

  it("renders rollout-disabled calibration evidence when recent traffic is gated", async () => {
    getTenantRecommendations.mockResolvedValueOnce({
      tenant_id: "tenant-alpha",
      generated_at: "2026-03-27T18:00:00Z",
      window_requests_evaluated: 4,
      calibration_summary: {
        tenant_id: "tenant-alpha",
        scope: "tenant",
        state: "thin",
        state_reason: "Calibrated routing remained disabled for recent tenant traffic.",
        generated_at: "2026-03-27T18:00:00Z",
        latest_eligible_request_at: null,
        latest_any_request_at: "2026-03-27T17:00:00Z",
        eligible_request_count: 0,
        sufficient_request_count: 0,
        thin_request_threshold: 5,
        staleness_threshold_hours: 24,
        excluded_request_count: 0,
        gated_request_count: 4,
        degraded_request_count: 0,
        excluded_reasons: [],
        gated_reasons: [{ reason: "calibrated_routing_disabled", count: 4 }],
        degraded_reasons: [],
      },
      recommendations: [],
      cache_summary: {
        enabled: true,
        similarity_threshold: 0.9,
        max_entry_age_hours: 168,
        runtime_status: "ready",
        runtime_detail: "Ready",
        estimated_hit_rate: 0.25,
        avoided_premium_cost_usd: 0.12,
        insights: [],
      },
    });

    renderPage();

    expect(await screen.findAllByText("Calibrated routing remained disabled for recent tenant traffic.")).toHaveLength(2);
    const followUpSection = screen.getByRole("heading", { name: "Follow-up context for the selected request" }).closest("section");
    expect(followUpSection).not.toBeNull();
    const followUp = within(followUpSection!);
    const replayReadinessHeading = followUp.getByRole("heading", { name: "Tenant-scoped replay readiness context" });
    const replayReadinessCard = replayReadinessHeading.closest("article");
    expect(replayReadinessCard).not.toBeNull();
    const replayReadiness = within(replayReadinessCard!);
    expect(replayReadiness.getByText("Rollout-disabled rows")).toBeInTheDocument();
    expect(replayReadiness.getByText("4")).toBeInTheDocument();
  });
});
