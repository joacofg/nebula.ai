import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PolicyForm } from "@/components/policy/policy-form";
import { renderWithProviders } from "@/test/render";

describe("policy-page", () => {
  it("renders grouped policy sections", () => {
    renderWithProviders(
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
          known_premium_models: ["openai/gpt-4o-mini"],
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
        onSave={vi.fn().mockResolvedValue(undefined)}
      />,
    );

    expect(screen.getByRole("heading", { name: "Runtime-enforced controls" })).toBeInTheDocument();
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
});
