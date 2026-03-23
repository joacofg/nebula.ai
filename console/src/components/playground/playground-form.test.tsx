import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PlaygroundForm } from "@/components/playground/playground-form";
import { renderWithProviders } from "@/test/render";

const tenants = [
  {
    id: "default",
    name: "Default Workspace",
    description: "Bootstrap tenant",
    metadata: {},
    active: true,
    created_at: "2026-03-16T12:00:00Z",
    updated_at: "2026-03-16T12:00:00Z",
  },
];

describe("playground-form", () => {
  it("submits the selected tenant and prompt", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    renderWithProviders(
      <PlaygroundForm
        tenants={tenants}
        selectedTenantId="default"
        model="nebula-auto"
        prompt="Hello from the playground"
        disabled={false}
        isSubmitting={false}
        sessionMissing={false}
        onSelectedTenantIdChange={vi.fn()}
        onModelChange={vi.fn()}
        onPromptChange={vi.fn()}
        onSubmit={onSubmit}
      />,
      { adminKey: "nebula-admin-key" },
    );

    expect(screen.getByRole("combobox", { name: /tenant/i })).toHaveValue("default");

    await user.click(screen.getByRole("button", { name: "Run prompt" }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it("blocks submission when the operator session is missing", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    renderWithProviders(
      <PlaygroundForm
        tenants={tenants}
        selectedTenantId="default"
        model="nebula-auto"
        prompt="Blocked prompt"
        disabled
        isSubmitting={false}
        sessionMissing
        onSelectedTenantIdChange={vi.fn()}
        onModelChange={vi.fn()}
        onPromptChange={vi.fn()}
        onSubmit={onSubmit}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Run prompt" }));

    expect(screen.getByText("Operator session missing.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Run prompt" })).toBeDisabled();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("explains the operator-only tenant-selected non-streaming flow", () => {
    renderWithProviders(
      <PlaygroundForm
        tenants={tenants}
        selectedTenantId="default"
        model="nebula-auto"
        prompt="Corroborate the current route"
        disabled={false}
        isSubmitting={false}
        sessionMissing={false}
        onSelectedTenantIdChange={vi.fn()}
        onModelChange={vi.fn()}
        onPromptChange={vi.fn()}
        onSubmit={vi.fn().mockResolvedValue(undefined)}
      />,
      { adminKey: "nebula-admin-key" },
    );

    expect(screen.getByRole("heading", { name: "Operator playground request" })).toBeInTheDocument();
    expect(
      screen.getByText(/Choose the tenant context on purpose, set the target model, and send one admin-session prompt/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/non-streaming playground path/i)).toBeInTheDocument();
    expect(
      screen.getByText(/The first response stays immediate and only shows completion content plus the request id/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/recorded ledger evidence appears after Nebula persists the outcome/i)).toBeInTheDocument();
  });
});
