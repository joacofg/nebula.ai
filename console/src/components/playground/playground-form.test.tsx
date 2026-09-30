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

    await user.click(screen.getByRole("button", { name: "Enviar" }));

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

    await user.click(screen.getByRole("button", { name: "Enviar" }));

    expect(screen.getByText("Falta la sesión de admin.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("loads an example prompt without sending it", async () => {
    const user = userEvent.setup();
    const onPromptChange = vi.fn();
    const onSubmit = vi.fn();

    renderWithProviders(
      <PlaygroundForm
        tenants={[{ id: "default", name: "Default Workspace", description: null, metadata: {}, active: true, created_at: "", updated_at: "" }]}
        selectedTenantId="default"
        model="nebula-auto"
        prompt=""
        disabled={false}
        isSubmitting={false}
        sessionMissing={false}
        onSelectedTenantIdChange={vi.fn()}
        onModelChange={vi.fn()}
        onPromptChange={onPromptChange}
        onSubmit={onSubmit}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Criba de Eratóstenes" }));
    expect(onPromptChange).toHaveBeenCalledWith(expect.stringContaining("criba de Eratóstenes"));
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Capital de Australia" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Boletos de avión" })).toBeInTheDocument();
  });
});
