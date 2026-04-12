import { screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ObservabilityPage from "@/app/(console)/observability/page";
import { renderWithProviders } from "@/test/render";

const adminApi = vi.hoisted(() => ({
  listTenants: vi.fn(),
  listUsageLedger: vi.fn(),
  getTenantRecommendations: vi.fn(),
}));

vi.mock("@/lib/admin-api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/admin-api")>("@/lib/admin-api");
  return {
    ...actual,
    listTenants: adminApi.listTenants,
    listUsageLedger: adminApi.listUsageLedger,
    getTenantRecommendations: adminApi.getTenantRecommendations,
  };
});

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

describe("observability-page", () => {
  it("frames observability around selected request evidence with bounded supporting context", async () => {
    adminApi.listTenants.mockResolvedValue([
      {
        id: "default",
        name: "Default Workspace",
        description: "Bootstrap tenant",
        metadata: {},
        active: true,
        created_at: "2026-03-16T12:00:00Z",
        updated_at: "2026-03-16T12:00:00Z",
      },
    ]);
    adminApi.listUsageLedger.mockResolvedValue([
      {
        request_id: "req-123",
        tenant_id: "default",
        requested_model: "nebula-auto",
        final_route_target: "premium",
        final_provider: "openai-compatible",
        fallback_used: false,
        cache_hit: false,
        response_model: "openai/gpt-4o-mini",
        prompt_tokens: 12,
        completion_tokens: 6,
        total_tokens: 18,
        estimated_cost: 0.012,
        latency_ms: 120,
        timestamp: "2026-03-16T22:00:00Z",
        terminal_status: "completed",
        route_reason: "direct_premium_model",
        policy_outcome: "allowed",
        route_signals: null,
        message_type: "chat",
        evidence_retention_window: "30d",
        evidence_expires_at: "2026-04-15T22:00:00Z",
        metadata_minimization_level: "standard",
        metadata_fields_suppressed: [],
        governance_source: "tenant_policy",
      },
    ]);
    adminApi.getTenantRecommendations.mockResolvedValue({
      tenant_id: "default",
      generated_at: "2026-03-27T18:00:00Z",
      window_requests_evaluated: 24,
      calibration_summary: {
        tenant_id: "default",
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
          code: "cache-tighten-threshold",
          title: "Tighten cache similarity threshold",
          priority: 1,
          category: "cache",
          summary: "Recent ledger-backed traffic shows reuse with mixed downstream outcomes.",
          recommended_action: "Raise the similarity threshold in policy preview before saving.",
          evidence: [
            { label: "Requests evaluated", value: "24" },
            { label: "Estimated hit rate", value: "42%" },
          ],
        },
      ],
      cache_summary: {
        enabled: true,
        similarity_threshold: 0.82,
        max_entry_age_hours: 48,
        runtime_status: "degraded",
        runtime_detail: "Qdrant latency is elevated but cache lookups still succeed.",
        estimated_hit_rate: 0.42,
        avoided_premium_cost_usd: 1.275,
        insights: [
          {
            code: "cache-health-watch",
            title: "Watch degraded cache runtime",
            level: "notice",
            summary: "Recent cache reuse remains valuable, but degraded runtime may reduce consistency.",
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
            postgres: { status: "healthy", required: true, detail: "reachable" },
            retention_lifecycle: {
              status: "degraded",
              required: false,
              detail: "Retention lifecycle cleanup failed on its last attempt.",
              last_status: "failed",
              last_run_at: "2026-04-12T01:02:03Z",
              last_attempted_run_at: "2026-04-12T01:05:00Z",
              last_deleted_count: 2,
              last_eligible_count: 2,
              last_error: "cleanup query timed out",
            },
          },
        }),
      }),
    );

    const { container } = renderWithProviders(<ObservabilityPage />, { adminKey: "nebula-admin-key" });

    expect(await screen.findByRole("heading", { name: "Selected request evidence first" })).toBeInTheDocument();
    expect(screen.getByText(/Start with one persisted ledger row for the selected request ID/i)).toBeInTheDocument();
    expect(screen.getByText(/supporting runtime context for that same routed request investigation/i)).toBeInTheDocument();

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
    expect(await screen.findAllByText("req-123")).toHaveLength(3);
    expect(await screen.findByText("Tighten cache similarity threshold")).toBeInTheDocument();

    const followUpSection = screen.getByRole("heading", { name: "Follow-up context for the selected request" }).closest("section");
    expect(followUpSection).not.toBeNull();
    expect(selectedRequestSection!.compareDocumentPosition(followUpSection!)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
    const selectedRequestText = selectedRequestSection!.textContent ?? "";
    const followUpText = followUpSection!.textContent ?? "";
    expect(selectedRequestText.indexOf("req-123")).toBeGreaterThanOrEqual(0);
    expect(followUpText.indexOf("retention_lifecycle")).toBeGreaterThanOrEqual(0);
    expect(selectedRequestText.indexOf("req-123")).toBeLessThan(
      container.firstElementChild!.textContent!.indexOf("retention_lifecycle"),
    );
    expect(followUpSection).not.toBeNull();
    const followUp = within(followUpSection!);
    expect(followUp.getByText(/use these supporting cards to decide the next operator action/i)).toBeInTheDocument();
    expect(followUp.getByText(/point toward policy preview as the comparison surface before any save elsewhere in the console/i)).toBeInTheDocument();

    const guidanceCard = followUp.getByRole("heading", { name: "Grounded follow-up guidance for the selected request" }).closest("article");
    expect(guidanceCard).not.toBeNull();
    const guidance = within(guidanceCard!);
    expect(guidance.getByText(/bounded operator guidance for the selected-request investigation/i)).toBeInTheDocument();
    expect(guidance.getByText(/Compare options in policy preview before saving any change elsewhere in the console/i)).toBeInTheDocument();

    expect(await followUp.findByText("Tighten cache similarity threshold")).toBeInTheDocument();
    expect(followUp.getByText(/Raise the similarity threshold in policy preview before saving/i)).toBeInTheDocument();

    const policyPreviewCard = followUp.getByRole("heading", { name: "Policy preview follow-up for the same request" }).closest("article");
    expect(policyPreviewCard).not.toBeNull();
    const policyPreview = within(policyPreviewCard!);
    expect(policyPreview.getByText(/Use calibration, cache, and dependency context to judge whether a policy preview comparison is grounded enough/i)).toBeInTheDocument();
    expect(policyPreview.getByText(/preview before saving in the policy editor/i)).toBeInTheDocument();
    expect(policyPreview.getByText(/keep the persisted request row as the authoritative evidence seam/i)).toBeInTheDocument();

    const calibrationCard = followUp.getByRole("heading", { name: "Tenant-scoped replay readiness context" }).closest("article");
    expect(calibrationCard).not.toBeNull();
    const calibration = within(calibrationCard!);
    expect(calibration.getByText(/before deciding whether a replay or policy preview comparison is grounded enough/i)).toBeInTheDocument();
    expect(calibration.getByText("Eligible calibrated rows")).toBeInTheDocument();
    expect(calibration.getByText("12")).toBeInTheDocument();
    expect(calibration.getByText("Sufficiency threshold")).toBeInTheDocument();
    expect(calibration.getByText("5")).toBeInTheDocument();
    expect(calibration.getByText(/Keep using the ledger row and request ID correlation as the primary proof\./i)).toBeInTheDocument();

    const cacheCard = followUp.getByRole("heading", { name: "Cache effectiveness and runtime controls" }).closest("section");
    expect(cacheCard).not.toBeNull();
    const cache = within(cacheCard!);
    expect(cache.getByText(/Use it to decide whether the next step is a policy preview comparison/i)).toBeInTheDocument();
    expect(cache.getByText(/this page stays inspection-only/i)).toBeInTheDocument();
    expect(cache.getByText("Similarity threshold")).toBeInTheDocument();
    expect(cache.getByText("0.82")).toBeInTheDocument();
    expect(cache.getByText("Max entry age")).toBeInTheDocument();
    expect(cache.getByText("48 hours")).toBeInTheDocument();

    const dependencySection = followUp.getByRole("heading", { name: "Dependency health context" }).closest("section");
    expect(dependencySection).not.toBeNull();
    const dependency = within(dependencySection!);
    expect(
      dependency.getByText(/These dependency states do not replace the ledger record; they provide supporting runtime context/i),
    ).toBeInTheDocument();
    expect(await dependency.findByText("retention_lifecycle")).toBeInTheDocument();
    expect(dependency.getByText("Last status")).toBeInTheDocument();
    expect(dependency.getByText("failed")).toBeInTheDocument();
    expect(dependency.getByText("Deleted rows")).toBeInTheDocument();
    expect(dependency.getAllByText("2")).toHaveLength(2);
    expect(dependency.getByText("cleanup query timed out")).toBeInTheDocument();
    expect(screen.queryByText(/retention dashboard/i)).not.toBeInTheDocument();

    vi.unstubAllGlobals();
  });
});
