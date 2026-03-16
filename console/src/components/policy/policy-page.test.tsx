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
        }}
        isSaving={false}
        onSave={vi.fn().mockResolvedValue(undefined)}
      />,
    );

    expect(screen.getByRole("heading", { name: "Routing mode" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Execution controls" })).toBeInTheDocument();
    expect(screen.getByText("Advanced settings")).toBeInTheDocument();
  });
});
