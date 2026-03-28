import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PolicyForm } from "@/components/policy/policy-form";
import type { PolicySimulationResponse } from "@/lib/admin-api";
import { renderWithProviders } from "@/test/render";

const baseSimulationResult: PolicySimulationResponse = {
  tenant_id: "default",
  candidate_policy: {
    routing_mode_default: "premium_only",
    fallback_enabled: false,
    semantic_cache_enabled: true,
    allowed_premium_models: ["openai/gpt-4o-mini"],
    max_premium_cost_per_request: 0.5,
    hard_budget_limit_usd: 10,
    hard_budget_enforcement: "deny",
    soft_budget_usd: null,
    prompt_capture_enabled: false,
    response_capture_enabled: false,
  },
  approximation_notes: ["Replay uses stored route signals rather than raw prompt text."],
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
    newly_denied: 1,
    baseline_premium_cost: 0.2,
    simulated_premium_cost: 0.3,
    premium_cost_delta: 0.1,
  },
  changed_requests: [
    {
      request_id: "req-1",
      timestamp: "2026-03-27T12:00:00Z",
      requested_model: "openai/gpt-4o-mini",
      baseline_route_target: "local",
      simulated_route_target: "premium",
      baseline_terminal_status: "completed",
      simulated_terminal_status: "policy_denied",
      baseline_policy_outcome: "default",
      simulated_policy_outcome: "routing_mode=premium_only;denied=Request exceeds the tenant premium spend guardrail.",
      baseline_route_reason: "auto_local",
      simulated_route_reason: "explicit_premium_model",
      baseline_estimated_cost: 0,
      simulated_estimated_cost: 0.1,
    },
  ],
};

function renderPolicyForm({
  onSave = vi.fn().mockResolvedValue(undefined),
  onSimulate = vi.fn().mockResolvedValue(undefined),
  simulationResult = null,
  simulationError = null,
  isSimulating = false,
} = {}) {
  return renderWithProviders(
    <PolicyForm
      tenantName="Default Workspace"
      initialPolicy={{
        routing_mode_default: "auto",
        fallback_enabled: true,
        semantic_cache_enabled: true,
        allowed_premium_models: ["openai/gpt-4o-mini"],
        max_premium_cost_per_request: null,
        hard_budget_limit_usd: null,
        hard_budget_enforcement: null,
        soft_budget_usd: null,
        prompt_capture_enabled: false,
        response_capture_enabled: false,
      }}
      options={{
        routing_modes: ["auto", "local_only", "premium_only"],
        known_premium_models: ["openai/gpt-4o-mini", "openai/gpt-4.1-mini"],
        default_premium_model: "openai/gpt-4o-mini",
        runtime_enforced_fields: [
          "routing_mode_default",
          "allowed_premium_models",
          "semantic_cache_enabled",
          "fallback_enabled",
          "max_premium_cost_per_request",
          "hard_budget_limit_usd",
          "hard_budget_enforcement",
        ],
        soft_signal_fields: ["soft_budget_usd"],
        advisory_fields: ["prompt_capture_enabled", "response_capture_enabled"],
      }}
      isSaving={false}
      isSimulating={isSimulating}
      simulationResult={simulationResult}
      simulationError={simulationError}
      onSimulate={onSimulate}
      onSave={onSave}
    />,
  );
}

describe("policy-form", () => {
  it("shows and clears dirty state with Reset changes", async () => {
    renderPolicyForm();

    await userEvent.selectOptions(screen.getByLabelText("Routing mode"), "premium_only");
    expect(screen.getByText("Unsaved changes")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Reset changes" }));

    expect(screen.queryByText("Unsaved changes")).not.toBeInTheDocument();
  });

  it("submits the updated policy payload", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    renderPolicyForm({ onSave });

    await userEvent.selectOptions(screen.getByLabelText("Routing mode"), "premium_only");
    await userEvent.click(screen.getByRole("checkbox", { name: "Fallback enabled" }));
    await userEvent.click(screen.getByRole("button", { name: "Save policy" }));

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith(
        expect.objectContaining({
          routing_mode_default: "premium_only",
          fallback_enabled: false,
        }),
      );
    });
  });

  it("sends the current draft to simulation without saving", async () => {
    const onSimulate = vi.fn().mockResolvedValue(undefined);
    const onSave = vi.fn().mockResolvedValue(undefined);
    renderPolicyForm({ onSimulate, onSave });

    await userEvent.selectOptions(screen.getByLabelText("Routing mode"), "premium_only");
    await userEvent.click(screen.getByRole("checkbox", { name: "Fallback enabled" }));
    await userEvent.click(screen.getByRole("button", { name: "Preview impact" }));

    await waitFor(() => {
      expect(onSimulate).toHaveBeenCalledWith(
        expect.objectContaining({
          routing_mode_default: "premium_only",
          fallback_enabled: false,
        }),
      );
    });
    expect(onSave).not.toHaveBeenCalled();
  });

  it("renders preview aggregates, changed requests, and replay notes without implying save", () => {
    renderPolicyForm({ simulationResult: baseSimulationResult });

    expect(screen.getByRole("heading", { name: "Preview before save" })).toBeInTheDocument();
    expect(screen.getByText("Save remains explicit")).toBeInTheDocument();
    expect(screen.getByText("Evaluated requests")).toBeInTheDocument();
    expect(screen.getByText("Changed routes")).toBeInTheDocument();
    expect(screen.getByText("Newly denied")).toBeInTheDocument();
    expect(screen.getByText("Premium cost delta")).toBeInTheDocument();
    expect(screen.getByText("Changed request sample")).toBeInTheDocument();
    expect(screen.getByText("req-1")).toBeInTheDocument();
    expect(screen.getByText(/route local → premium/i)).toBeInTheDocument();
    expect(screen.getByText(/status completed → policy_denied/i)).toBeInTheDocument();
    expect(screen.getByText(/Replay uses stored route signals rather than raw prompt text./i)).toBeInTheDocument();
    expect(screen.getByText(/This preview did not save the policy./i)).toBeInTheDocument();
  });

  it("renders explicit empty and error preview states", () => {
    const { rerender } = renderPolicyForm({
      simulationResult: {
        ...baseSimulationResult,
        window: {
          ...baseSimulationResult.window,
          returned_rows: 0,
        },
        summary: {
          ...baseSimulationResult.summary,
          evaluated_rows: 0,
          changed_routes: 0,
          newly_denied: 0,
          premium_cost_delta: 0,
        },
        changed_requests: [],
      },
    });

    expect(
      screen.getByText("No recent traffic matched the replay window, so there was nothing to preview."),
    ).toBeInTheDocument();

    rerender(
      <PolicyForm
        tenantName="Default Workspace"
        initialPolicy={{
          routing_mode_default: "auto",
          fallback_enabled: true,
          semantic_cache_enabled: true,
          allowed_premium_models: ["openai/gpt-4o-mini"],
          max_premium_cost_per_request: null,
          soft_budget_usd: null,
          prompt_capture_enabled: false,
          response_capture_enabled: false,
        }}
        options={{
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
        }}
        isSaving={false}
        isSimulating={false}
        simulationResult={null}
        simulationError="Nebula admin request failed."
        onSimulate={vi.fn().mockResolvedValue(undefined)}
        onSave={vi.fn().mockResolvedValue(undefined)}
      />,
    );

    expect(screen.getByText("Preview failed: Nebula admin request failed.")).toBeInTheDocument();
  });

  it("derives runtime-enforced controls from policy options and keeps soft budget outside that section", () => {
    renderPolicyForm();

    const runtimeSection = screen.getByRole("heading", { name: "Runtime-enforced controls" }).closest("section");
    expect(runtimeSection).not.toBeNull();
    expect(runtimeSection).toHaveTextContent("Routing mode");
    expect(runtimeSection).toHaveTextContent("Fallback enabled");
    expect(runtimeSection).toHaveTextContent("Semantic cache enabled");
    expect(runtimeSection).toHaveTextContent("Premium model allowlist");
    expect(runtimeSection).toHaveTextContent("Max premium cost per request");
    expect(runtimeSection).toHaveTextContent("Hard cumulative budget limit USD");
    expect(runtimeSection).toHaveTextContent("Hard budget enforcement");
    expect(runtimeSection).not.toHaveTextContent("Soft budget USD");

    expect(
      screen.getByText(
        "Soft budget signal only. Adds policy outcome metadata when exceeded but does not block routing in Phase 4.",
      ),
    ).toBeInTheDocument();
  });
});
