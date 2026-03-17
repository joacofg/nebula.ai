import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PolicyForm } from "@/components/policy/policy-form";
import { renderWithProviders } from "@/test/render";

function renderPolicyForm(onSave = vi.fn().mockResolvedValue(undefined)) {
  return renderWithProviders(
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
    renderPolicyForm(onSave);

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

  it("derives runtime-enforced controls from policy options and keeps soft budget outside that section", () => {
    renderPolicyForm();

    const runtimeSection = screen.getByRole("heading", { name: "Runtime-enforced controls" }).closest("section");
    expect(runtimeSection).not.toBeNull();
    expect(runtimeSection).toHaveTextContent("Routing mode");
    expect(runtimeSection).toHaveTextContent("Fallback enabled");
    expect(runtimeSection).toHaveTextContent("Semantic cache enabled");
    expect(runtimeSection).toHaveTextContent("Premium model allowlist");
    expect(runtimeSection).toHaveTextContent("Max premium cost per request");
    expect(runtimeSection).not.toHaveTextContent("Soft budget USD");

    expect(
      screen.getByText(
        "Soft budget signal only. Adds policy outcome metadata when exceeded but does not block routing in Phase 4.",
      ),
    ).toBeInTheDocument();
  });
});
