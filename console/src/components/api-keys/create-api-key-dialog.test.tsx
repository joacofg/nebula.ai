import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { CreateApiKeyDialog } from "@/components/api-keys/create-api-key-dialog";
import { renderWithProviders } from "@/test/render";

const TENANTS = [
  {
    id: "tenant-a",
    name: "Tenant A",
    description: "Primary",
    metadata: {},
    active: true,
    created_at: "2026-03-16T12:00:00Z",
    updated_at: "2026-03-16T12:00:00Z",
  },
  {
    id: "tenant-b",
    name: "Tenant B",
    description: "Secondary",
    metadata: {},
    active: true,
    created_at: "2026-03-16T12:00:00Z",
    updated_at: "2026-03-16T12:00:00Z",
  },
];

describe("create-api-key-dialog", () => {
  it("titles the dialog and explains the tenant header in one line", () => {
    renderWithProviders(
      <CreateApiKeyDialog
        open
        tenants={TENANTS}
        selectedTenantId="tenant-a"
        isSaving={false}
        onClose={vi.fn()}
        onSubmit={vi.fn().mockResolvedValue(undefined)}
      />,
    );

    expect(screen.getByRole("heading", { name: "Nueva clave de API" })).toBeInTheDocument();
    expect(screen.getByText("La clave se muestra una sola vez al crearla.")).toBeInTheDocument();
    expect(screen.getByText(/Con más de uno y sin tenant por defecto, los pedidos envían X-Nebula-Tenant-ID/)).toBeInTheDocument();
  });

  it("requires at least one allowed tenant", async () => {
    renderWithProviders(
      <CreateApiKeyDialog
        open
        tenants={TENANTS}
        selectedTenantId="tenant-a"
        isSaving={false}
        onClose={vi.fn()}
        onSubmit={vi.fn().mockResolvedValue(undefined)}
      />,
    );

    await userEvent.type(screen.getByLabelText("Nombre"), "Test key");
    await userEvent.click(screen.getByLabelText("Tenant A"));
    await userEvent.click(screen.getByRole("button", { name: "Crear clave" }));

    expect(screen.getByText("Elegir al menos un tenant permitido.")).toBeInTheDocument();
  });

  it("submits tenant scope choices", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    renderWithProviders(
      <CreateApiKeyDialog
        open
        tenants={TENANTS}
        selectedTenantId="tenant-a"
        isSaving={false}
        onClose={vi.fn()}
        onSubmit={onSubmit}
      />,
    );

    await userEvent.type(screen.getByLabelText("Nombre"), "Console key");
    await userEvent.click(screen.getByLabelText("Tenant B"));
    await userEvent.click(screen.getByRole("button", { name: "Crear clave" }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        name: "Console key",
        tenant_id: "tenant-a",
        allowed_tenant_ids: ["tenant-a", "tenant-b"],
      });
    });
  });
});

describe("create-api-key-dialog focus", () => {
  it("keeps keyboard focus inside the dialog and closes on Escape", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderWithProviders(
      <>
        <button type="button">Outside</button>
        <CreateApiKeyDialog
          open
          tenants={TENANTS}
          selectedTenantId="tenant-a"
          isSaving={false}
          onClose={onClose}
          onSubmit={vi.fn().mockResolvedValue(undefined)}
        />
      </>,
    );
    const dialog = screen.getByRole("dialog");
    for (let i = 0; i < 8; i += 1) {
      await user.tab();
      expect(dialog).toContainElement(document.activeElement as HTMLElement);
    }
    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalled();
  });
});
