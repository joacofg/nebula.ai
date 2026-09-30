import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TenantEditorDrawer } from "@/components/tenants/tenant-editor-drawer";
import { renderWithProviders } from "@/test/render";

describe("tenant-editor-drawer", () => {
  it("keeps id readOnly during edit", () => {
    renderWithProviders(
      <TenantEditorDrawer
        mode="edit"
        tenant={{
          id: "tenant-a",
          name: "Tenant A",
          description: "Primary",
          metadata: { tier: "gold" },
          active: true,
          created_at: "2026-03-16T12:00:00Z",
          updated_at: "2026-03-16T12:00:00Z",
        }}
        isSaving={false}
        onClose={vi.fn()}
        onSubmit={vi.fn().mockResolvedValue(undefined)}
      />,
    );

    expect(screen.getByLabelText("Id")).toHaveAttribute("readonly");
  });

  it("titles a new tenant and keeps one line of help for metadata", () => {
    renderWithProviders(
      <TenantEditorDrawer mode="create" tenant={null} isSaving={false} onClose={vi.fn()} onSubmit={vi.fn()} />,
    );
    expect(screen.getByRole("heading", { name: "Nuevo tenant" })).toBeInTheDocument();
    expect(screen.getByText("Notas del operador; Nebula no valida su esquema.")).toBeInTheDocument();
  });

  it("validates metadata JSON before submit", async () => {
    renderWithProviders(
      <TenantEditorDrawer
        mode="create"
        tenant={null}
        isSaving={false}
        onClose={vi.fn()}
        onSubmit={vi.fn().mockResolvedValue(undefined)}
      />,
    );

    await userEvent.type(screen.getByLabelText("Id"), "new-team");
    await userEvent.type(screen.getByLabelText("Nombre"), "New Team");
    await userEvent.clear(screen.getByLabelText("Metadatos"));
    await userEvent.type(screen.getByLabelText("Metadatos"), "bad json");
    await userEvent.click(screen.getByRole("button", { name: "Crear tenant" }));

    expect(screen.getByText("Los metadatos tienen que ser JSON válido.")).toBeInTheDocument();
  });

  it("submits normalized tenant payload", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    renderWithProviders(
      <TenantEditorDrawer
        mode="create"
        tenant={null}
        isSaving={false}
        onClose={vi.fn()}
        onSubmit={onSubmit}
      />,
    );

    await userEvent.type(screen.getByLabelText("Id"), "tenant-b");
    await userEvent.type(screen.getByLabelText("Nombre"), "Tenant B");
    await userEvent.click(screen.getByRole("button", { name: "Crear tenant" }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          id: "tenant-b",
          name: "Tenant B",
          active: true,
        }),
      );
    });
  });
});
