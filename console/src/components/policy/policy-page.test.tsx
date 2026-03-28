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
  ]);
  getTenantPolicyMock.mockResolvedValue({
    routing_mode_default: "auto",
    fallback_enabled: true,
    semantic_cache_enabled: true,
    allowed_premium_models: ["openai/gpt-4o-mini"],
    max_premium_cost_per_request: null,
    soft_budget_usd: null,
    prompt_capture_enabled: false,
    response_capture_enabled: false,
  });
  getPolicyOptionsMock.mockResolvedValue({
    routing_modes: ["auto", "local_only", "premium_only"],
    known_premium_models: ["openai/gpt-4o-mini", "openai/gpt-4.1-mini"],
    default_premium_model: "openai/gpt-4o-mini",
    runtime_enforced_fields: [
      "routing_mode_default",
      "allowed_premium_models",
      "semantic_cache_enabled",
      "fallback_enabled",
      "max_premium_cost_per_request",
    ],
    soft_signal_fields: ["soft_budget_usd"],
    advisory_fields: ["prompt_capture_enabled", "response_capture_enabled"],
  });
  updateTenantPolicyMock.mockResolvedValue({
    routing_mode_default: "premium_only",
    fallback_enabled: true,
    semantic_cache_enabled: true,
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
      fallback_enabled: true,
      semantic_cache_enabled: true,
      allowed_premium_models: ["openai/gpt-4o-mini"],
      max_premium_cost_per_request: null,
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
      returned_rows: 1,
    },
    summary: {
      evaluated_rows: 1,
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
        baseline_route_reason: "auto_local",
        simulated_route_reason: "explicit_premium_model",
        baseline_estimated_cost: 0,
        simulated_estimated_cost: 0.01,
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
        "Capture settings are deferred for a future governance/privacy phase and are not editable in Phase 4.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Soft budget signal only. Adds policy outcome metadata when exceeded but does not block routing in Phase 4.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText("Prompt capture enabled")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Response capture enabled")).not.toBeInTheDocument();
  });

  it("previews the current draft without saving and keeps save explicit", async () => {
    renderPolicyPage();

    await screen.findByRole("heading", { name: "Preview before save" });
    await userEvent.selectOptions(screen.getByLabelText("Routing mode"), "premium_only");
    await userEvent.click(screen.getByRole("button", { name: "Preview impact" }));

    await waitFor(() => {
      expect(simulateTenantPolicyMock).toHaveBeenCalledWith(
        "admin-key",
        "tenant-a",
        expect.objectContaining({
          candidate_policy: expect.objectContaining({ routing_mode_default: "premium_only" }),
          limit: 50,
          changed_sample_limit: 5,
        }),
      );
    });

    expect(updateTenantPolicyMock).not.toHaveBeenCalled();
    expect(await screen.findByText("Changed request sample")).toBeInTheDocument();
    expect(screen.getByText(/This preview did not save the policy./i)).toBeInTheDocument();
    expect(screen.getByText("Save remains explicit")).toBeInTheDocument();
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
  });

  it("shows explicit zero-result preview state", async () => {
    simulateTenantPolicyMock.mockResolvedValueOnce({
      tenant_id: "tenant-a",
      candidate_policy: {
        routing_mode_default: "auto",
        fallback_enabled: true,
        semantic_cache_enabled: true,
        allowed_premium_models: ["openai/gpt-4o-mini"],
        max_premium_cost_per_request: null,
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
    expect(updateTenantPolicyMock).not.toHaveBeenCalled();
  });
});

