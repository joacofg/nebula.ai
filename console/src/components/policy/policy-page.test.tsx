import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";

import PolicyPage from "@/app/(console)/policy/page";
import * as adminApi from "@/lib/admin-api";
import { renderWithProviders } from "@/test/render";

vi.mock("@/lib/admin-api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/admin-api")>("@/lib/admin-api");
  return {
    ...actual,
    listTenants: vi.fn(),
    getTenantPolicy: vi.fn(),
    getPolicyOptions: vi.fn(),
    updateTenantPolicy: vi.fn(),
    simulateTenantPolicy: vi.fn(),
  };
});

const listTenantsMock = vi.mocked(adminApi.listTenants);
const getTenantPolicyMock = vi.mocked(adminApi.getTenantPolicy);
const getPolicyOptionsMock = vi.mocked(adminApi.getPolicyOptions);
const updateTenantPolicyMock = vi.mocked(adminApi.updateTenantPolicy);
const simulateTenantPolicyMock = vi.mocked(adminApi.simulateTenantPolicy);

function renderPolicyPage() {
  return renderWithProviders(<PolicyPage />, { adminKey: "admin-key" });
}

beforeEach(() => {
  vi.clearAllMocks();

  listTenantsMock.mockResolvedValue([
    {
      id: "tenant-a",
      name: "Tenant A",
      description: null,
      metadata: {},
      active: true,
      created_at: "2026-03-27T00:00:00Z",
      updated_at: "2026-03-27T00:00:00Z",
    },
    {
      id: "tenant-b",
      name: "Tenant B",
      description: null,
      metadata: {},
      active: true,
      created_at: "2026-03-28T00:00:00Z",
      updated_at: "2026-03-28T00:00:00Z",
    },
  ]);
  getTenantPolicyMock.mockImplementation(async (_adminKey, tenantId) => ({
    routing_mode_default: tenantId === "tenant-b" ? "local_only" : "auto",
    fallback_enabled: tenantId === "tenant-b" ? false : true,
    semantic_cache_enabled: true,
    semantic_cache_similarity_threshold: tenantId === "tenant-b" ? 0.88 : 0.9,
    semantic_cache_max_entry_age_hours: tenantId === "tenant-b" ? 72 : 168,
    allowed_premium_models: ["openai/gpt-4o-mini"],
    max_premium_cost_per_request: null,
    hard_budget_limit_usd: null,
    hard_budget_enforcement: null,
    soft_budget_usd: null,
    prompt_capture_enabled: false,
    response_capture_enabled: false,
  }));
  getPolicyOptionsMock.mockResolvedValue({
    routing_modes: ["auto", "local_only", "premium_only"],
    known_premium_models: ["openai/gpt-4o-mini", "openai/gpt-4.1-mini"],
    default_premium_model: "openai/gpt-4o-mini",
    runtime_enforced_fields: [
      "routing_mode_default",
      "allowed_premium_models",
      "semantic_cache_enabled",
      "semantic_cache_similarity_threshold",
      "semantic_cache_max_entry_age_hours",
      "fallback_enabled",
      "max_premium_cost_per_request",
      "hard_budget_limit_usd",
      "hard_budget_enforcement",
    ],
    soft_signal_fields: ["soft_budget_usd"],
    advisory_fields: ["prompt_capture_enabled", "response_capture_enabled"],
  });
  updateTenantPolicyMock.mockResolvedValue({
    routing_mode_default: "premium_only",
    fallback_enabled: true,
    semantic_cache_enabled: true,
    semantic_cache_similarity_threshold: 0.82,
    semantic_cache_max_entry_age_hours: 48,
    allowed_premium_models: ["openai/gpt-4o-mini"],
    max_premium_cost_per_request: null,
    hard_budget_limit_usd: 20,
    hard_budget_enforcement: "downgrade",
    soft_budget_usd: null,
    prompt_capture_enabled: false,
    response_capture_enabled: false,
  });
  simulateTenantPolicyMock.mockResolvedValue({
    tenant_id: "tenant-a",
    candidate_policy: {
      routing_mode_default: "premium_only",
      calibrated_routing_enabled: false,
      fallback_enabled: true,
      semantic_cache_enabled: true,
      semantic_cache_similarity_threshold: 0.82,
      semantic_cache_max_entry_age_hours: 48,
      allowed_premium_models: ["openai/gpt-4o-mini"],
      max_premium_cost_per_request: null,
      hard_budget_limit_usd: 20,
      hard_budget_enforcement: "downgrade",
      soft_budget_usd: null,
      prompt_capture_enabled: false,
      response_capture_enabled: false,
    },
    approximation_notes: ["Replay uses stored route signals."],
    window: {
      requested_from: null,
      requested_to: null,
      evaluated_from: "2026-03-27T00:00:00Z",
      evaluated_to: "2026-03-28T00:00:00Z",
      requested_limit: 50,
      changed_sample_limit: 5,
      returned_rows: 2,
    },
    summary: {
      evaluated_rows: 2,
      changed_routes: 1,
      newly_denied: 0,
      baseline_premium_cost: 0,
      simulated_premium_cost: 0.01,
      premium_cost_delta: 0.01,
    },
    changed_requests: [
      {
        request_id: "req-1",
        timestamp: "2026-03-27T12:00:00Z",
        requested_model: "nebula-auto",
        baseline_route_target: "local",
        simulated_route_target: "premium",
        baseline_terminal_status: "completed",
        simulated_terminal_status: "completed",
        baseline_policy_outcome: "default",
        simulated_policy_outcome: "routing_mode=premium_only",
        baseline_route_reason: "token_complexity",
        simulated_route_reason: "token_complexity",
        baseline_route_mode: "calibrated",
        simulated_route_mode: "degraded",
        baseline_calibrated_routing: true,
        simulated_calibrated_routing: false,
        baseline_degraded_routing: false,
        simulated_degraded_routing: true,
        baseline_route_score: 0.74,
        simulated_route_score: 0.31,
        baseline_estimated_cost: 0,
        simulated_estimated_cost: 0.01,
      },
      {
        request_id: "req-2",
        timestamp: "2026-03-27T13:00:00Z",
        requested_model: "nebula-auto",
        baseline_route_target: "local",
        simulated_route_target: "local",
        baseline_terminal_status: "completed",
        simulated_terminal_status: "completed",
        baseline_policy_outcome: "default",
        simulated_policy_outcome: "default",
        baseline_route_reason: "token_complexity",
        simulated_route_reason: "calibrated_routing_disabled",
        baseline_route_mode: "degraded",
        simulated_route_mode: null,
        baseline_calibrated_routing: false,
        simulated_calibrated_routing: null,
        baseline_degraded_routing: true,
        simulated_degraded_routing: null,
        baseline_route_score: 0.28,
        simulated_route_score: null,
        baseline_estimated_cost: 0,
        simulated_estimated_cost: 0,
      },
    ],
  });
});

describe("policy-page", () => {
  it("renders grouped policy sections", async () => {
    renderPolicyPage();

    expect(await screen.findByRole("heading", { name: "Runtime-enforced controls" })).toBeInTheDocument();
    expect(
      screen.getByText(
        "These controls change live routing behavior. Hard budget settings are cumulative tenant spend guardrails, not advisory reporting thresholds.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "When the hard cumulative budget is exhausted, Nebula either downgrades compatible auto-routed traffic to local or denies premium routing, depending on the enforcement mode below.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Applies in live request evaluation")).toBeInTheDocument();
    expect(screen.getByLabelText("Semantic cache similarity threshold")).toBeInTheDocument();
    expect(screen.getByLabelText("Semantic cache max entry age hours")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Runtime-enforced cache controls stay in this policy editor. Adjust them deliberately, preview the draft against recent ledger-backed traffic, and save explicitly when the evidence supports the change.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Load a tenant policy, compare the current baseline against a candidate draft using recent persisted traffic, and save explicitly only after the preview evidence supports the change.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Higher values require a closer semantic match before Nebula reuses a cached response.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Lower values age out cached entries sooner when recent traffic suggests stale reuse risk.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Soft budget advisory" })).toBeInTheDocument();
    expect(
      screen.getByText(
        "Advisory only. Exceeding this threshold adds operator-visible policy outcome metadata, but it does not block, downgrade, or deny routing.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Capture settings are deferred for a future governance/privacy phase and are not editable in Phase 4.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText("Prompt capture enabled")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Response capture enabled")).not.toBeInTheDocument();
  });

  it("previews the current draft without saving and keeps save explicit", async () => {
    renderPolicyPage();

    await screen.findByRole("heading", { name: "Preview before save" });
    await userEvent.selectOptions(screen.getByLabelText("Routing mode"), "premium_only");
    await userEvent.clear(screen.getByLabelText("Semantic cache similarity threshold"));
    await userEvent.type(screen.getByLabelText("Semantic cache similarity threshold"), "0.82");
    await userEvent.clear(screen.getByLabelText("Semantic cache max entry age hours"));
    await userEvent.type(screen.getByLabelText("Semantic cache max entry age hours"), "48");
    await userEvent.click(screen.getByRole("button", { name: "Preview impact" }));

    await waitFor(() => {
      expect(simulateTenantPolicyMock).toHaveBeenCalledWith(
        "admin-key",
        "tenant-a",
        expect.objectContaining({
          candidate_policy: expect.objectContaining({
            routing_mode_default: "premium_only",
            semantic_cache_similarity_threshold: 0.82,
            semantic_cache_max_entry_age_hours: 48,
          }),
          limit: 50,
          changed_sample_limit: 5,
        }),
      );
    });

    expect(updateTenantPolicyMock).not.toHaveBeenCalled();
    expect(await screen.findByText("Changed request sample")).toBeInTheDocument();
    expect(
      screen.getByText(
        /Bounded sample of persisted requests whose route, status, policy outcome, or projected cost changed between the current baseline and this draft\./i,
      ),
    ).toBeInTheDocument();
    expect(screen.getByText(/Compared 2 recent persisted request\(s\) against this draft baseline\./i)).toBeInTheDocument();
    expect(screen.getByText(/This preview did not save the policy./i)).toBeInTheDocument();
    expect(screen.getByText("Save remains explicit")).toBeInTheDocument();
    expect(
      screen.getByText(
        "routing parity: calibrated (calibrated, score 0.74) → degraded (degraded, score 0.31)",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("routing parity: degraded (degraded, score 0.28) → rollout disabled"),
    ).toBeInTheDocument();
    expect(screen.queryByText(/dashboard/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/routing studio/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/analytics product/i)).not.toBeInTheDocument();
  });

  it("shows preview errors from the simulation mutation", async () => {
    simulateTenantPolicyMock.mockRejectedValueOnce(new Error("from_timestamp must be less than or equal to to_timestamp."));
    renderPolicyPage();

    await screen.findByRole("heading", { name: "Preview before save" });
    await userEvent.click(screen.getByRole("button", { name: "Preview impact" }));

    expect(
      await screen.findByText(
        "Preview failed: from_timestamp must be less than or equal to to_timestamp.",
      ),
    ).toBeInTheDocument();
    expect(updateTenantPolicyMock).not.toHaveBeenCalled();
    expect(screen.queryByText(/dashboard/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/routing studio/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/analytics product/i)).not.toBeInTheDocument();
  });

  it("shows explicit zero-result preview state", async () => {
    simulateTenantPolicyMock.mockResolvedValueOnce({
      tenant_id: "tenant-a",
      candidate_policy: {
        routing_mode_default: "auto",
        fallback_enabled: true,
        semantic_cache_enabled: true,
        semantic_cache_similarity_threshold: 0.9,
        semantic_cache_max_entry_age_hours: 168,
        allowed_premium_models: ["openai/gpt-4o-mini"],
        max_premium_cost_per_request: null,
        hard_budget_limit_usd: null,
        hard_budget_enforcement: null,
        soft_budget_usd: null,
        prompt_capture_enabled: false,
        response_capture_enabled: false,
      },
      approximation_notes: [],
      window: {
        requested_from: null,
        requested_to: null,
        evaluated_from: null,
        evaluated_to: null,
        requested_limit: 50,
        changed_sample_limit: 5,
        returned_rows: 0,
      },
      summary: {
        evaluated_rows: 0,
        changed_routes: 0,
        newly_denied: 0,
        baseline_premium_cost: 0,
        simulated_premium_cost: 0,
        premium_cost_delta: 0,
      },
      changed_requests: [],
    });

    renderPolicyPage();

    await screen.findByRole("heading", { name: "Preview before save" });
    await userEvent.click(screen.getByRole("button", { name: "Preview impact" }));

    expect(
      await screen.findByText("No recent traffic matched the replay window, so there was nothing to preview."),
    ).toBeInTheDocument();
    expect(screen.getByText(/This preview did not save the policy./i)).toBeInTheDocument();
    expect(updateTenantPolicyMock).not.toHaveBeenCalled();
    expect(screen.queryByText(/dashboard/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/routing studio/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/analytics product/i)).not.toBeInTheDocument();
  });

  it("keeps unchanged previews explicitly non-saving", async () => {
    simulateTenantPolicyMock.mockResolvedValueOnce({
      tenant_id: "tenant-a",
      candidate_policy: {
        routing_mode_default: "auto",
        fallback_enabled: true,
        semantic_cache_enabled: true,
        semantic_cache_similarity_threshold: 0.9,
        semantic_cache_max_entry_age_hours: 168,
        allowed_premium_models: ["openai/gpt-4o-mini"],
        max_premium_cost_per_request: null,
        hard_budget_limit_usd: null,
        hard_budget_enforcement: null,
        soft_budget_usd: null,
        prompt_capture_enabled: false,
        response_capture_enabled: false,
      },
      approximation_notes: [],
      window: {
        requested_from: null,
        requested_to: null,
        evaluated_from: "2026-03-27T00:00:00Z",
        evaluated_to: "2026-03-28T00:00:00Z",
        requested_limit: 50,
        changed_sample_limit: 5,
        returned_rows: 3,
      },
      summary: {
        evaluated_rows: 3,
        changed_routes: 0,
        newly_denied: 0,
        baseline_premium_cost: 0,
        simulated_premium_cost: 0,
        premium_cost_delta: 0,
      },
      changed_requests: [],
    });

    renderPolicyPage();

    await screen.findByRole("heading", { name: "Preview before save" });
    await userEvent.click(screen.getByRole("button", { name: "Preview impact" }));

    expect(await screen.findByText("No decision pressure")).toBeInTheDocument();
    expect(screen.getByText("This draft leaves the sampled baseline unchanged.")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Keep iterating if you expected a different outcome, or save when you want these settings persisted without changing recent request outcomes.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Next step: save only if the unchanged replay matches your intent.")).toBeInTheDocument();
    expect(screen.getByText(/This preview did not save the policy./i)).toBeInTheDocument();
    expect(updateTenantPolicyMock).not.toHaveBeenCalled();
  });

  it("clears stale preview evidence after a successful save", async () => {
    renderPolicyPage();

    await screen.findByRole("heading", { name: "Preview before save" });
    await userEvent.selectOptions(screen.getByLabelText("Routing mode"), "premium_only");
    await userEvent.clear(screen.getByLabelText("Semantic cache similarity threshold"));
    await userEvent.type(screen.getByLabelText("Semantic cache similarity threshold"), "0.82");
    await userEvent.clear(screen.getByLabelText("Semantic cache max entry age hours"));
    await userEvent.type(screen.getByLabelText("Semantic cache max entry age hours"), "48");
    await userEvent.click(screen.getByRole("button", { name: "Preview impact" }));

    expect(await screen.findByText("Changed request sample")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Save policy" }));

    await waitFor(() => {
      expect(updateTenantPolicyMock).toHaveBeenCalledWith(
        "admin-key",
        "tenant-a",
        expect.objectContaining({
          routing_mode_default: "premium_only",
          semantic_cache_similarity_threshold: 0.82,
          semantic_cache_max_entry_age_hours: 48,
        }),
      );
    });

    await waitFor(() => {
      expect(screen.queryByText("Changed request sample")).not.toBeInTheDocument();
    });
    expect(
      screen.getByText("Run a preview to compare this draft against recent ledger-backed requests before saving."),
    ).toBeInTheDocument();
  });

  it("clears stale preview evidence when switching tenants", async () => {
    renderPolicyPage();

    await screen.findByRole("heading", { name: "Preview before save" });
    await userEvent.click(screen.getByRole("button", { name: "Preview impact" }));

    expect(await screen.findByText("Changed request sample")).toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("Tenant"), "tenant-b");

    await waitFor(() => {
      expect(getTenantPolicyMock).toHaveBeenCalledWith("admin-key", "tenant-b");
    });
    await waitFor(() => {
      expect(screen.queryByText("Changed request sample")).not.toBeInTheDocument();
    });
    expect(
      screen.getByText("Run a preview to compare this draft against recent ledger-backed requests before saving."),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Policy for Tenant B" })).toBeInTheDocument();
    expect(screen.getByText("Load a tenant policy, compare the current baseline against a candidate draft using recent persisted traffic, and save explicitly only after the preview evidence supports the change.")).toBeInTheDocument();
  });
});
