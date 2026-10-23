import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TenantEditorDrawer } from "@/components/tenants/tenant-editor-drawer";
import { renderWithProviders } from "@/test/render";

const TENANT_A = {
  id: "tenant-a",
  name: "Tenant A",
  description: "Primary",
  metadata: {},
  active: true,
  created_at: "2026-03-16T12:00:00Z",
  updated_at: "2026-03-16T12:00:00Z",
};

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

  it("focuses the first field when asked to, on mount and again later", () => {
    const view = renderWithProviders(
      <TenantEditorDrawer mode="create" tenant={null} isSaving={false} focusRequest={0} onClose={vi.fn()} onSubmit={vi.fn()} />,
    );
    expect(screen.getByLabelText("Id")).not.toHaveFocus();

    view.rerender(
      <TenantEditorDrawer mode="create" tenant={null} isSaving={false} focusRequest={1} onClose={vi.fn()} onSubmit={vi.fn()} />,
    );
    expect(screen.getByLabelText("Id")).toHaveFocus();

    screen.getByLabelText("Nombre").focus();
    view.rerender(
      <TenantEditorDrawer mode="create" tenant={null} isSaving={false} focusRequest={2} onClose={vi.fn()} onSubmit={vi.fn()} />,
    );
    expect(screen.getByLabelText("Id")).toHaveFocus();
  });

  it("says what happened in a status line", () => {
    renderWithProviders(
      <TenantEditorDrawer
        mode="edit"
        tenant={TENANT_A}
        notice="Tenant creado."
        isSaving={false}
        onClose={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(screen.getByRole("status")).toHaveTextContent("Tenant creado.");
    expect(screen.getByRole("heading", { name: "Editar Tenant A" })).toBeInTheDocument();
  });

  it("keeps what the operator typed when the same tenant is read again", async () => {
    const view = renderWithProviders(
      <TenantEditorDrawer mode="edit" tenant={TENANT_A} isSaving={false} onClose={vi.fn()} onSubmit={vi.fn()} />,
    );
    await userEvent.clear(screen.getByLabelText("Nombre"));
    await userEvent.type(screen.getByLabelText("Nombre"), "Tenant renombrado");

    view.rerender(
      <TenantEditorDrawer
        mode="edit"
        tenant={{ ...TENANT_A, updated_at: "2026-03-17T12:00:00Z" }}
        isSaving={false}
        onClose={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    expect(screen.getByLabelText("Nombre")).toHaveValue("Tenant renombrado");
  });

  it("loads another tenant's record when the tenant changes", () => {
    const view = renderWithProviders(
      <TenantEditorDrawer mode="edit" tenant={TENANT_A} isSaving={false} onClose={vi.fn()} onSubmit={vi.fn()} />,
    );
    view.rerender(
      <TenantEditorDrawer
        mode="edit"
        tenant={{ ...TENANT_A, id: "tenant-b", name: "Tenant B" }}
        isSaving={false}
        onClose={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(screen.getByLabelText("Id")).toHaveValue("tenant-b");
    expect(screen.getByLabelText("Nombre")).toHaveValue("Tenant B");
  });

  it("closes through Cerrar", async () => {
    const onClose = vi.fn();
    renderWithProviders(
      <TenantEditorDrawer mode="edit" tenant={TENANT_A} isSaving={false} onClose={onClose} onSubmit={vi.fn()} />,
    );
    await userEvent.click(screen.getByRole("button", { name: "Cerrar" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
