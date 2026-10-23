import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { CreateApiKeyDialog } from "@/components/api-keys/create-api-key-dialog";
import { renderWithProviders } from "@/test/render";
import { TENANT_A } from "@/test/tenants";

const TENANTS = [TENANT_A, { ...TENANT_A, id: "tenant-b", name: "Tenant B", description: "Secondary" }];

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

  it("offers no default tenant first and submits it as null", async () => {
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

    const select = screen.getByLabelText("Tenant por defecto");
    expect(within(select).getAllByRole("option").map((option) => option.textContent)).toEqual([
      "Sin tenant por defecto",
      "Tenant A",
      "Tenant B",
    ]);
    expect(select).toHaveValue("tenant-a");

    await userEvent.selectOptions(select, "Sin tenant por defecto");
    expect(select).toHaveValue("");

    await userEvent.type(screen.getByLabelText("Nombre"), "Header key");
    await userEvent.click(screen.getByLabelText("Tenant B"));
    await userEvent.click(screen.getByRole("button", { name: "Crear clave" }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        name: "Header key",
        tenant_id: null,
        allowed_tenant_ids: ["tenant-a", "tenant-b"],
      });
    });
  });

  it("shows the empty option when there are no tenants to default to", () => {
    renderWithProviders(
      <CreateApiKeyDialog
        open
        tenants={[]}
        selectedTenantId={null}
        isSaving={false}
        onClose={vi.fn()}
        onSubmit={vi.fn().mockResolvedValue(undefined)}
      />,
    );

    const select = screen.getByLabelText("Tenant por defecto");
    expect(select).toHaveValue("");
    expect(within(select).getByRole("option", { name: "Sin tenant por defecto" })).toBeInTheDocument();
  });

  it("links the tenant-header hint to the controls it explains", () => {
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

    const hint = /Con más de uno y sin tenant por defecto, los pedidos envían X-Nebula-Tenant-ID/;
    expect(screen.getByRole("group", { name: "Tenants permitidos" })).toHaveAccessibleDescription(hint);
    expect(screen.getByLabelText("Tenant por defecto")).toHaveAccessibleDescription(hint);
  });
});

describe("create-api-key-dialog ids", () => {
  it("renders two dialogs with distinct input ids", () => {
    renderWithProviders(
      <>
        {[0, 1].map((index) => (
          <CreateApiKeyDialog
            key={index}
            open
            tenants={TENANTS}
            selectedTenantId="tenant-a"
            isSaving={false}
            onClose={vi.fn()}
            onSubmit={vi.fn().mockResolvedValue(undefined)}
          />
        ))}
      </>,
    );

    expect(screen.getAllByRole("dialog", { hidden: true })).toHaveLength(2);
    const ids = Array.from(document.querySelectorAll("[id]")).map((element) => element.id);
    expect(ids.length).toBeGreaterThan(0);
    expect(new Set(ids).size).toBe(ids.length);
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
