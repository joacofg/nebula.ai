import { within } from "@testing-library/react";
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
    calibrated_routing_enabled: true,
    fallback_enabled: false,
    semantic_cache_enabled: true,
    semantic_cache_similarity_threshold: 0.9,
    semantic_cache_max_entry_age_hours: 168,
    allowed_premium_models: ["openai/gpt-4o-mini"],
    max_premium_cost_per_request: 0.5,
    hard_budget_limit_usd: 10,
    hard_budget_enforcement: "deny",
    soft_budget_usd: null,
    prompt_capture_enabled: false,
    response_capture_enabled: false,
    evidence_retention_window: "30d",
    metadata_minimization_level: "standard",
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
  calibration_summary: {
    tenant_id: "default",
    scope: "tenant_window",
    state: "thin",
    state_reason: "Eligible calibrated routing evidence is still below the tenant sufficiency threshold.",
    generated_at: "2026-03-28T00:00:00Z",
    latest_eligible_request_at: "2026-03-28T00:00:00Z",
    latest_any_request_at: "2026-03-28T00:00:00Z",
    eligible_request_count: 2,
    sufficient_request_count: 2,
    thin_request_threshold: 5,
    staleness_threshold_hours: 24,
    excluded_request_count: 0,
    gated_request_count: 0,
    degraded_request_count: 0,
    excluded_reasons: [],
    gated_reasons: [],
    degraded_reasons: [],
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
      baseline_route_mode: "auto",
      simulated_route_mode: "premium_only",
      baseline_calibrated_routing: true,
      simulated_calibrated_routing: null,
      baseline_degraded_routing: false,
      simulated_degraded_routing: false,
      baseline_route_score: 0.61,
      simulated_route_score: null,
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
        calibrated_routing_enabled: true,
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
        evidence_retention_window: "30d",
        metadata_minimization_level: "standard",
      }}
      options={{
        routing_modes: ["auto", "local_only", "premium_only"],
        known_premium_models: ["openai/gpt-4o-mini", "openai/gpt-4.1-mini"],
        default_premium_model: "openai/gpt-4o-mini",
        runtime_enforced_fields: [
          "routing_mode_default",
          "calibrated_routing_enabled",
          "allowed_premium_models",
          "semantic_cache_enabled",
          "semantic_cache_similarity_threshold",
          "semantic_cache_max_entry_age_hours",
          "fallback_enabled",
          "max_premium_cost_per_request",
          "hard_budget_limit_usd",
          "hard_budget_enforcement",
          "evidence_retention_window",
          "metadata_minimization_level",
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
    await userEvent.clear(screen.getByLabelText("Semantic cache similarity threshold"));
    await userEvent.type(screen.getByLabelText("Semantic cache similarity threshold"), "0.82");
    await userEvent.clear(screen.getByLabelText("Semantic cache max entry age hours"));
    await userEvent.type(screen.getByLabelText("Semantic cache max entry age hours"), "48");
    await userEvent.click(screen.getByRole("button", { name: "Save policy" }));

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith(
        expect.objectContaining({
          routing_mode_default: "premium_only",
          calibrated_routing_enabled: true,
          fallback_enabled: false,
          semantic_cache_similarity_threshold: 0.82,
          semantic_cache_max_entry_age_hours: 48,
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
    await userEvent.clear(screen.getByLabelText("Semantic cache similarity threshold"));
    await userEvent.type(screen.getByLabelText("Semantic cache similarity threshold"), "0.88");
    await userEvent.click(screen.getByRole("button", { name: "Preview impact" }));

    await waitFor(() => {
      expect(onSimulate).toHaveBeenCalledWith(
        expect.objectContaining({
          routing_mode_default: "premium_only",
          fallback_enabled: false,
          semantic_cache_similarity_threshold: 0.88,
        }),
      );
    });
    expect(onSave).not.toHaveBeenCalled();
  });

  it("renders a decision-first preview with bounded evidence and explicit save separation", () => {
    renderPolicyForm({ simulationResult: baseSimulationResult });

    const previewSection = screen.getByRole("heading", { name: "Preview before save" }).closest("section");
    expect(previewSection).not.toBeNull();
    const preview = within(previewSection as HTMLElement);

    expect(preview.getByText("Review before save")).toBeInTheDocument();
    expect(preview.getByText("Preview only — save stays separate.")).toBeInTheDocument();
    expect(
      preview.getByText(
        "Compared with the current baseline, this draft would change 1 sampled request.",
      ),
    ).toBeInTheDocument();
    expect(
      preview.getByText(
        /Operator consequence: 1 sampled request would route differently; 1 request would become denied; premium spend would increase by \$0\.1000\./i,
      ),
    ).toBeInTheDocument();
    expect(
      preview.getByText(
        "Next step: keep iterating if those denials are not intentional, or save only when you want that draft enforced live.",
      ),
    ).toBeInTheDocument();
    expect(preview.getByText("Save remains explicit")).toBeInTheDocument();
    expect(preview.getByText("Evaluated requests")).toBeInTheDocument();
    expect(preview.getByText("Changed routes")).toBeInTheDocument();
    expect(preview.getByText("Newly denied")).toBeInTheDocument();
    expect(preview.getByText("Premium cost delta")).toBeInTheDocument();
    expect(preview.getByText("Changed request sample")).toBeInTheDocument();
    expect(preview.getByText("req-1")).toBeInTheDocument();
    expect(preview.getByText(/route local → premium/i)).toBeInTheDocument();
    expect(preview.getByText(/status completed → policy_denied/i)).toBeInTheDocument();
    expect(preview.getByText(/routing parity: auto \(calibrated, score 0\.61\) → premium_only/i)).toBeInTheDocument();
    expect(
      preview.getByText(
        /Supporting evidence only: bounded sample of persisted requests whose route, status, policy outcome, or projected cost changed between the current baseline and this draft\./i,
      ),
    ).toBeInTheDocument();
    expect(preview.getByText(/Replay uses stored route signals rather than raw prompt text\./i)).toBeInTheDocument();
    expect(preview.getByText(/Compared 2 recent persisted request\(s\) against this draft baseline\./i)).toBeInTheDocument();
    expect(preview.getByText(/This preview did not save the policy\./i)).toBeInTheDocument();
    expect(screen.queryByText(/dashboard/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/routing studio/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/analytics product/i)).not.toBeInTheDocument();
  });

  it("keeps unchanged, empty, loading, and failed preview states explicit and non-saving", () => {
    const unchangedResult: PolicySimulationResponse = {
      ...baseSimulationResult,
      summary: {
        ...baseSimulationResult.summary,
        changed_routes: 0,
        newly_denied: 0,
        premium_cost_delta: 0,
      },
      changed_requests: [],
    };

    const { rerender } = renderPolicyForm({ simulationResult: unchangedResult });

    let previewSection = screen.getByRole("heading", { name: "Preview before save" }).closest("section");
    expect(previewSection).not.toBeNull();
    let preview = within(previewSection as HTMLElement);

    expect(preview.getByText("No decision pressure")).toBeInTheDocument();
    expect(preview.getByText("This draft leaves the sampled baseline unchanged.")).toBeInTheDocument();
    expect(
      preview.getByText(
        "Keep iterating if you expected a different outcome, or save when you want these settings persisted without changing recent request outcomes.",
      ),
    ).toBeInTheDocument();
    expect(
      preview.getByText("Next step: save only if the unchanged replay matches your intent."),
    ).toBeInTheDocument();
    expect(preview.getByText("No request outcomes changed in this replay window.")).toBeInTheDocument();
    expect(preview.getByText(/This preview did not save the policy\./i)).toBeInTheDocument();

    rerender(
      <PolicyForm
        tenantName="Default Workspace"
        initialPolicy={{
          routing_mode_default: "auto",
          calibrated_routing_enabled: true,
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
        }}
        options={{
          routing_modes: ["auto", "local_only", "premium_only"],
          known_premium_models: ["openai/gpt-4o-mini", "openai/gpt-4.1-mini"],
          default_premium_model: "openai/gpt-4o-mini",
          runtime_enforced_fields: [
            "routing_mode_default",
            "calibrated_routing_enabled",
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
        }}
        isSaving={false}
        isSimulating={false}
        simulationResult={{
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
        }}
        simulationError={null}
        onSimulate={vi.fn().mockResolvedValue(undefined)}
        onSave={vi.fn().mockResolvedValue(undefined)}
      />,
    );

    previewSection = screen.getByRole("heading", { name: "Preview before save" }).closest("section");
    expect(previewSection).not.toBeNull();
    preview = within(previewSection as HTMLElement);

    expect(preview.getByText("No comparison window")).toBeInTheDocument();
    expect(preview.getByText("No recent baseline matched this preview window.")).toBeInTheDocument();
    expect(
      preview.getByText(
        "Keep iterating in the editor if the draft still needs work, or save only when you intend to publish without replay evidence.",
      ),
    ).toBeInTheDocument();
    expect(
      preview.getByText("Next step: preview again after recent persisted traffic is available."),
    ).toBeInTheDocument();
    expect(
      preview.getByText("No recent traffic matched the replay window, so there was nothing to preview."),
    ).toBeInTheDocument();
    expect(preview.getByText(/This preview did not save the policy\./i)).toBeInTheDocument();

    rerender(
      <PolicyForm
        tenantName="Default Workspace"
        initialPolicy={{
          routing_mode_default: "auto",
          calibrated_routing_enabled: true,
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
        }}
        options={{
          routing_modes: ["auto", "local_only", "premium_only"],
          known_premium_models: ["openai/gpt-4o-mini", "openai/gpt-4.1-mini"],
          default_premium_model: "openai/gpt-4o-mini",
          runtime_enforced_fields: [
            "routing_mode_default",
            "calibrated_routing_enabled",
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
        }}
        isSaving={false}
        isSimulating={true}
        simulationResult={null}
        simulationError={null}
        onSimulate={vi.fn().mockResolvedValue(undefined)}
        onSave={vi.fn().mockResolvedValue(undefined)}
      />,
    );

    expect(screen.getByText("Simulating draft policy against recent tenant traffic...")).toBeInTheDocument();
    expect(screen.queryByText(/save policy/i)).toBeInTheDocument();

    rerender(
      <PolicyForm
        tenantName="Default Workspace"
        initialPolicy={{
          routing_mode_default: "auto",
          calibrated_routing_enabled: true,
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
        }}
        options={{
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
    expect(screen.queryByText(/dashboard/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/routing studio/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/analytics product/i)).not.toBeInTheDocument();
  });

  it("renders malformed and rollout-disabled routing parity without crashing", () => {
    renderPolicyForm({
      simulationResult: {
        ...baseSimulationResult,
        summary: {
          ...baseSimulationResult.summary,
          changed_routes: 0,
          newly_denied: 0,
          premium_cost_delta: 0.025,
        },
        changed_requests: [
          {
            ...baseSimulationResult.changed_requests[0],
            request_id: "req-rollout-disabled",
            baseline_route_mode: null,
            baseline_calibrated_routing: null,
            baseline_degraded_routing: null,
            baseline_route_score: null,
            baseline_route_reason: "calibrated_routing_disabled",
            simulated_route_mode: null,
            simulated_calibrated_routing: null,
            simulated_degraded_routing: true,
            simulated_route_score: null,
            simulated_route_reason: null,
            baseline_route_target: "local",
            simulated_route_target: "local",
            baseline_terminal_status: "completed",
            simulated_terminal_status: "completed",
            baseline_policy_outcome: "default",
            simulated_policy_outcome: "soft_budget_warning",
            baseline_estimated_cost: 0.05,
            simulated_estimated_cost: 0.075,
          },
        ],
      },
    });

    expect(
      screen.getByText(
        "Compared with the current baseline, this draft would change 1 sampled request.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Operator consequence: premium spend would increase by \$0\.0250\./i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/routing parity: rollout disabled → unscored \(degraded\)/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/policy default → soft_budget_warning/i)).toBeInTheDocument();
  });

  it("derives runtime-enforced controls from policy options and keeps soft budget outside that section", () => {
    renderPolicyForm();

    const runtimeSection = screen.getByRole("heading", { name: "Runtime-enforced controls" }).closest("section");
    expect(runtimeSection).not.toBeNull();
    expect(runtimeSection).toHaveTextContent("Routing mode");
    expect(runtimeSection).toHaveTextContent("Calibrated routing enabled");
    expect(runtimeSection).toHaveTextContent("Fallback enabled");
    expect(runtimeSection).toHaveTextContent("Semantic cache enabled");
    expect(runtimeSection).toHaveTextContent("Semantic cache similarity threshold");
    expect(runtimeSection).toHaveTextContent("Semantic cache max entry age hours");
    expect(runtimeSection).toHaveTextContent("Premium model allowlist");
    expect(runtimeSection).toHaveTextContent("Max premium cost per request");
    expect(runtimeSection).toHaveTextContent("Hard cumulative budget limit USD");
    expect(runtimeSection).toHaveTextContent("Hard budget enforcement");
    expect(runtimeSection).toHaveTextContent("Applies in live request evaluation");
    expect(runtimeSection).toHaveTextContent(
      "These controls change live routing behavior. Hard budget settings are cumulative tenant spend guardrails, not advisory reporting thresholds.",
    );
    expect(runtimeSection).toHaveTextContent(
      "When the hard cumulative budget is exhausted, Nebula either downgrades compatible auto-routed traffic to local or denies premium routing, depending on the enforcement mode below.",
    );
    expect(runtimeSection).toHaveTextContent(
      "Runtime-enforced cache controls stay in this policy editor. Adjust them deliberately, preview the draft against recent ledger-backed traffic, and save explicitly when the evidence supports the change.",
    );
    expect(runtimeSection).toHaveTextContent("Effective evidence boundary");
    expect(runtimeSection).toHaveTextContent(
      "Runtime-enforced guidance derived from the retention and minimization controls below.",
    );
    expect(runtimeSection).toHaveTextContent("Local runtime evidence");
    expect(runtimeSection).toHaveTextContent(
      "Nebula keeps governed request metadata historically inspectable for up to 30 days before expiration markers say it should age out.",
    );
    expect(runtimeSection).toHaveTextContent(
      "While a retained row exists, operators can inspect bounded ledger metadata such as tenant, model, route, status, and governance markers.",
    );
    expect(runtimeSection).toHaveTextContent(
      "Standard minimization preserves route signals and other governed metadata when Nebula can safely retain them for later inspection.",
    );
    expect(runtimeSection).toHaveTextContent(
      "Hosted export still excludes raw usage-ledger rows; operators must confirm serving-time behavior from local runtime surfaces.",
    );
    expect(runtimeSection).toHaveTextContent(
      "Runtime-enforced evidence retention sets how long governed ledger metadata remains historically inspectable before expiration markers say it should age out.",
    );
    expect(runtimeSection).toHaveTextContent(
      "Strict minimization suppresses governed metadata fields like route signals at write time; standard preserves them when available for operator inspection.",
    );
    expect(runtimeSection).toHaveTextContent(
      "Higher values require a closer semantic match before Nebula reuses a cached response.",
    );
    expect(runtimeSection).toHaveTextContent(
      "Lower values age out cached entries sooner when recent traffic suggests stale reuse risk.",
    );
    expect(runtimeSection).not.toHaveTextContent("Soft budget USD");

    expect(screen.getByRole("heading", { name: "Soft budget advisory" })).toBeInTheDocument();
    expect(
      screen.getByText(
        "Advisory only. Exceeding this threshold adds operator-visible policy outcome metadata, but it does not block, downgrade, or deny routing.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Use this to flag spend pressure for operators. Use the hard budget controls above when tenant traffic must change at runtime.",
      ),
    ).toBeInTheDocument();
  });

  it("updates the effective evidence boundary copy when strict minimization is selected", async () => {
    renderPolicyForm();

    await userEvent.selectOptions(screen.getByLabelText("Metadata minimization level"), "strict");

    const runtimeSection = screen.getByRole("heading", { name: "Runtime-enforced controls" }).closest("section");
    expect(runtimeSection).not.toBeNull();
    expect(runtimeSection).toHaveTextContent(
      "While a retained row exists, operators can still inspect bounded ledger metadata such as tenant, model, status, and governance markers.",
    );
    expect(runtimeSection).toHaveTextContent(
      "Strict minimization suppresses route signals and other minimizable metadata at write time, so that detail is no longer available later from the ledger.",
    );
    expect(runtimeSection).toHaveTextContent(
      "Hosted export still excludes raw usage-ledger rows; operators must confirm serving-time behavior from local runtime surfaces.",
    );
  });

  it("blocks save when cache tuning values are outside the enforced bounds", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    renderPolicyForm({ onSave });

    await userEvent.clear(screen.getByLabelText("Semantic cache similarity threshold"));
    await userEvent.type(screen.getByLabelText("Semantic cache similarity threshold"), "1.2");
    await userEvent.click(screen.getByRole("button", { name: "Save policy" }));

    expect(
      await screen.findByText("Semantic cache similarity threshold must be between 0 and 1."),
    ).toBeInTheDocument();
    expect(onSave).not.toHaveBeenCalled();
  });

  it("disables hard-budget enforcement selection until a hard limit is configured", async () => {
    renderPolicyForm();

    const enforcementSelect = screen.getByLabelText("Hard budget enforcement");
    expect(enforcementSelect).toBeDisabled();
    expect(
      screen.getByText("Set a hard cumulative budget limit first to activate this enforcement choice."),
    ).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText("Hard cumulative budget limit USD"), "25");

    expect(screen.getByLabelText("Hard budget enforcement")).toBeEnabled();
    expect(
      screen.getByText(
        "Applies when cumulative premium spend reaches the hard budget limit. Explicit premium requests still deny when downgrade is not allowed.",
      ),
    ).toBeInTheDocument();
  });
});
;
