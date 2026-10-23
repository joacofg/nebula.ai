import { onlineManager } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/admin-session-provider", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/admin-session-provider")>();
  return {
    ...actual,
    useAdminSession: vi.fn(),
  };
});

vi.mock("@/lib/admin-api", () => ({
  ADMIN_TENANTS_ENDPOINT: "/v1/admin/tenants",
  createTenant: vi.fn(),
  listTenants: vi.fn(),
  updateTenant: vi.fn(),
}));

import TenantsPage from "@/app/(console)/tenants/page";
import { useAdminSession } from "@/lib/admin-session-provider";
import { createTenant, listTenants, updateTenant } from "@/lib/admin-api";
import { renderWithProviders } from "@/test/render";

const mockedUseAdminSession = vi.mocked(useAdminSession);
const mockedListTenants = vi.mocked(listTenants);

const TENANT_A = {
  id: "tenant-a",
  name: "Tenant A",
  description: "Primary tenant",
  metadata: {},
  active: true,
  created_at: "2026-03-16T12:00:00Z",
  updated_at: "2026-03-16T12:00:00Z",
};
const TENANT_B = { ...TENANT_A, id: "tenant-b", name: "Tenant B", description: "Second tenant" };

beforeEach(() => {
  mockedUseAdminSession.mockReturnValue({
    adminKey: "admin-key",
    isAuthenticated: true,
    isSigningIn: false,
    signIn: vi.fn().mockResolvedValue(undefined),
    signOut: vi.fn(),
    clearSession: vi.fn(),
  });

  mockedListTenants.mockResolvedValue([TENANT_A]);
});

describe("tenants page", () => {
  it("titles the page and counts active tenants", async () => {
    renderWithProviders(<TenantsPage />);

    expect(await screen.findByRole("heading", { level: 1, name: "Tenants" })).toBeInTheDocument();
    expect(await screen.findByText("1 activos")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Crear tenant" })).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Buscar por id o nombre")).toBeInTheDocument();
  });

  it("shows the error when the tenant list fails", async () => {
    mockedListTenants.mockRejectedValue(new Error("Tenants unavailable."));
    renderWithProviders(<TenantsPage />);
    expect(await screen.findByText("Tenants unavailable.")).toBeInTheDocument();
  });

  it("keeps loading, with no drawer, and does not claim there are no tenants while the gateway cannot be reached", async () => {
    mockedListTenants.mockClear();
    onlineManager.setOnline(false);
    try {
      renderWithProviders(<TenantsPage />);
      // Offline, TanStack pauses a query that has no data: not loading, not failed, just waiting.
      await new Promise((resolve) => setTimeout(resolve, 50));

      expect(mockedListTenants).not.toHaveBeenCalled();
      expect(screen.getByRole("status", { name: "Cargando tenants" })).toBeInTheDocument();
      expect(screen.queryByText("Todavía no hay tenants.")).not.toBeInTheDocument();
      expect(screen.queryByRole("heading", { name: "Nuevo tenant" })).not.toBeInTheDocument();
    } finally {
      onlineManager.setOnline(true);
    }
  });

  it("offers to create the first tenant when there are none", async () => {
    mockedListTenants.mockResolvedValue([]);
    renderWithProviders(<TenantsPage />);
    expect(await screen.findByText("Todavía no hay tenants.")).toBeInTheDocument();
  });

  it("keeps the editor open and shows why creating a tenant failed", async () => {
    vi.mocked(createTenant).mockRejectedValue(new Error("Ya existe un recurso con ese identificador."));
    const user = userEvent.setup();
    renderWithProviders(<TenantsPage />);
    await screen.findByText("Tenant A");

    await user.click(screen.getByRole("button", { name: "Crear tenant" }));
    await user.type(screen.getByLabelText("Id"), "tenant-a");
    await user.type(screen.getByLabelText("Nombre"), "Tenant A");
    await user.click(screen.getAllByRole("button", { name: "Crear tenant" })[1]);

    expect(await screen.findByRole("alert")).toHaveTextContent("Ya existe un recurso con ese identificador.");
    expect(screen.getByLabelText("Id")).toHaveValue("tenant-a");
  });

  it("says when the search matches no tenant", async () => {
    renderWithProviders(<TenantsPage />);
    await screen.findByText("Tenant A");

    await userEvent.type(screen.getByPlaceholderText("Buscar por id o nombre"), "zzz");

    expect(screen.getByText("Sin resultados.")).toBeInTheDocument();
    expect(screen.queryByRole("table", { name: "Tenants" })).not.toBeInTheDocument();
  });

  it("opens the first tenant for editing and closes the drawer with Cerrar", async () => {
    const user = userEvent.setup();
    renderWithProviders(<TenantsPage />);

    expect(await screen.findByRole("heading", { name: "Editar Tenant A" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Cerrar" }));

    expect(screen.queryByRole("heading", { name: /Editar|Nuevo tenant/ })).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Id")).not.toBeInTheDocument();
    expect(screen.getByRole("table", { name: "Tenants" })).toBeInTheDocument();
  });

  it("closes a drawer opened to create a tenant without leaving an empty editor behind", async () => {
    const user = userEvent.setup();
    renderWithProviders(<TenantsPage />);
    await screen.findByRole("heading", { name: "Editar Tenant A" });

    await user.click(screen.getByRole("button", { name: "Crear tenant" }));
    expect(screen.getByRole("heading", { name: "Nuevo tenant" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Cerrar" }));

    expect(screen.queryByRole("heading", { name: /Editar|Nuevo tenant/ })).not.toBeInTheDocument();
    expect(screen.queryByText("Editar tenant")).not.toBeInTheDocument();
  });

  it("opens a tenant again from the table after closing the drawer", async () => {
    const user = userEvent.setup();
    mockedListTenants.mockResolvedValue([TENANT_A, TENANT_B]);
    renderWithProviders(<TenantsPage />);
    await screen.findByRole("heading", { name: "Editar Tenant A" });
    await user.click(screen.getByRole("button", { name: "Cerrar" }));

    await user.click(screen.getByRole("row", { name: /Tenant B/ }));

    expect(screen.getByRole("heading", { name: "Editar Tenant B" })).toBeInTheDocument();
    expect(screen.getByRole("row", { name: /Tenant B/ })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("row", { name: /Tenant A/ })).toHaveAttribute("aria-selected", "false");
  });

  it("moves focus to the first field when Crear tenant is pressed, also after closing", async () => {
    const user = userEvent.setup();
    renderWithProviders(<TenantsPage />);
    await screen.findByRole("heading", { name: "Editar Tenant A" });

    await user.click(screen.getByRole("button", { name: "Crear tenant" }));
    expect(screen.getByLabelText("Id")).toHaveFocus();

    await user.click(screen.getByRole("button", { name: "Cerrar" }));
    await user.click(screen.getByRole("button", { name: "Crear tenant" }));
    expect(screen.getByLabelText("Id")).toHaveFocus();

    await user.click(screen.getByLabelText("Nombre"));
    await user.click(screen.getAllByRole("button", { name: "Crear tenant" })[0]);
    expect(screen.getByLabelText("Id")).toHaveFocus();
  });

  it("returns focus to Crear tenant when the drawer it opened is closed from the keyboard", async () => {
    const user = userEvent.setup();
    renderWithProviders(<TenantsPage />);
    await screen.findByRole("heading", { name: "Editar Tenant A" });
    const create = screen.getByRole("button", { name: "Crear tenant" });

    create.focus();
    await user.keyboard("{Enter}");
    expect(screen.getByLabelText("Id")).toHaveFocus();
    await user.tab({ shift: true });
    expect(screen.getByRole("button", { name: "Cerrar" })).toHaveFocus();
    await user.keyboard("{Enter}");

    expect(screen.queryByLabelText("Id")).not.toBeInTheDocument();
    expect(create).toHaveFocus();
  });

  it("returns focus to the selected row when the drawer that edits it is closed from the keyboard", async () => {
    const user = userEvent.setup();
    mockedListTenants.mockResolvedValue([TENANT_A, TENANT_B]);
    renderWithProviders(<TenantsPage />);
    await screen.findByRole("heading", { name: "Editar Tenant A" });

    // The drawer is open on the first tenant from the start: Cerrar hands focus to its row.
    screen.getByRole("button", { name: "Cerrar" }).focus();
    await user.keyboard("{Enter}");
    expect(screen.getByRole("row", { name: /Tenant A/ })).toHaveFocus();

    // Opened from a row with Enter, it goes back to that row.
    screen.getByRole("row", { name: /Tenant B/ }).focus();
    await user.keyboard("{Enter}");
    expect(await screen.findByRole("heading", { name: "Editar Tenant B" })).toBeInTheDocument();
    screen.getByRole("button", { name: "Cerrar" }).focus();
    await user.keyboard("{Enter}");

    expect(screen.queryByRole("heading", { name: /Editar/ })).not.toBeInTheDocument();
    expect(screen.getByRole("row", { name: /Tenant B/ })).toHaveFocus();
  });

  it("returns focus to Crear tenant when the row of the tenant being edited is filtered out", async () => {
    const user = userEvent.setup();
    mockedListTenants.mockResolvedValue([TENANT_A, TENANT_B]);
    renderWithProviders(<TenantsPage />);
    await screen.findByRole("heading", { name: "Editar Tenant A" });

    await user.type(screen.getByPlaceholderText("Buscar por id o nombre"), "tenant-b");
    expect(screen.queryByRole("row", { name: /Tenant A/ })).not.toBeInTheDocument();
    screen.getByRole("button", { name: "Cerrar" }).focus();
    await user.keyboard("{Enter}");

    expect(screen.queryByRole("heading", { name: /Editar/ })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Crear tenant" })).toHaveFocus();
  });

  it("returns focus to the Crear tenant that was pressed, the one in the empty state or the header's", async () => {
    const user = userEvent.setup();
    mockedListTenants.mockResolvedValue([]);
    renderWithProviders(<TenantsPage />);
    await screen.findByText("Todavía no hay tenants.");

    // The drawer was never opened by a control here: focus goes to the page's own Crear tenant.
    await user.click(screen.getByRole("button", { name: "Cerrar" }));
    const [header, empty] = screen.getAllByRole("button", { name: "Crear tenant" });
    expect(header).toHaveFocus();

    empty.focus();
    await user.keyboard("{Enter}");
    await user.click(screen.getByRole("button", { name: "Cerrar" }));
    expect(empty).toHaveFocus();
  });

  it("confirms the new tenant and opens it for editing", async () => {
    const user = userEvent.setup();
    vi.mocked(createTenant).mockImplementation(async () => {
      mockedListTenants.mockResolvedValue([TENANT_A, TENANT_B]);
      return TENANT_B;
    });
    renderWithProviders(<TenantsPage />);
    await screen.findByRole("heading", { name: "Editar Tenant A" });

    await user.click(screen.getByRole("button", { name: "Crear tenant" }));
    await user.type(screen.getByLabelText("Id"), "tenant-b");
    await user.type(screen.getByLabelText("Nombre"), "Tenant B");
    await user.click(screen.getAllByRole("button", { name: "Crear tenant" })[1]);

    expect(await screen.findByRole("status")).toHaveTextContent("Tenant creado.");
    expect(screen.getByRole("heading", { name: "Editar Tenant B" })).toBeInTheDocument();
    expect(screen.getByLabelText("Id")).toHaveValue("tenant-b");
    expect(screen.getByLabelText("Id")).toHaveAttribute("readonly");
    expect(screen.getByRole("button", { name: "Guardar tenant" })).toBeInTheDocument();
    expect(await screen.findByRole("row", { name: /Tenant B/ })).toHaveAttribute("aria-selected", "true");

    // The confirmation belongs to that save: picking another tenant clears it.
    await user.click(within(screen.getByRole("table", { name: "Tenants" })).getByRole("row", { name: /Tenant A/ }));
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("confirms a saved edit with 'Tenant guardado.' until the next edit", async () => {
    const user = userEvent.setup();
    vi.mocked(updateTenant).mockImplementation(async (_key, id, payload) => ({ ...TENANT_A, ...payload, id }));
    renderWithProviders(<TenantsPage />);
    await screen.findByRole("heading", { name: "Editar Tenant A" });

    await user.clear(screen.getByLabelText("Descripción"));
    await user.type(screen.getByLabelText("Descripción"), "Edited");
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Guardar tenant" }));

    expect(await screen.findByRole("status")).toHaveTextContent("Tenant guardado.");
    expect(vi.mocked(updateTenant)).toHaveBeenCalledWith("admin-key", "tenant-a", expect.objectContaining({ description: "Edited" }));

    // The confirmation belongs to that save: the next edit takes it away.
    await user.type(screen.getByLabelText("Descripción"), "!");
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("does not confirm an edit the gateway refused", async () => {
    const user = userEvent.setup();
    vi.mocked(updateTenant).mockRejectedValue(new Error("No se encontró el recurso."));
    renderWithProviders(<TenantsPage />);
    await screen.findByRole("heading", { name: "Editar Tenant A" });

    await user.click(screen.getByRole("button", { name: "Guardar tenant" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("No se encontró el recurso.");
    expect(screen.queryByText("Tenant guardado.")).not.toBeInTheDocument();
  });

  it("shows no drawer while the tenants load, and a new-tenant form when there are none", async () => {
    mockedListTenants.mockResolvedValue([]);
    renderWithProviders(<TenantsPage />);

    expect(screen.queryByLabelText("Id")).not.toBeInTheDocument();
    expect(await screen.findByText("Todavía no hay tenants.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Nuevo tenant" })).toBeInTheDocument();
  });
});
