import userEvent from "@testing-library/user-event";
import { screen } from "@testing-library/react";
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
import { listTenants } from "@/lib/admin-api";
import { renderWithProviders } from "@/test/render";

const mockedUseAdminSession = vi.mocked(useAdminSession);
const mockedListTenants = vi.mocked(listTenants);

beforeEach(() => {
  mockedUseAdminSession.mockReturnValue({
    adminKey: "admin-key",
    isAuthenticated: true,
    isSigningIn: false,
    signIn: vi.fn().mockResolvedValue(undefined),
    signOut: vi.fn(),
    clearSession: vi.fn(),
  });

  mockedListTenants.mockResolvedValue([
    {
      id: "tenant-a",
      name: "Tenant A",
      description: "Primary tenant",
      metadata: {},
      active: true,
      created_at: "2026-03-16T12:00:00Z",
      updated_at: "2026-03-16T12:00:00Z",
    },
  ]);
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

  it("offers to create the first tenant when there are none", async () => {
    mockedListTenants.mockResolvedValue([]);
    renderWithProviders(<TenantsPage />);
    expect(await screen.findByText("Todavía no hay tenants.")).toBeInTheDocument();
  });

  it("says when the search matches no tenant", async () => {
    renderWithProviders(<TenantsPage />);
    await screen.findByText("Tenant A");

    await userEvent.type(screen.getByPlaceholderText("Buscar por id o nombre"), "zzz");

    expect(screen.getByText("Sin resultados.")).toBeInTheDocument();
    expect(screen.queryByRole("table", { name: "Tenants" })).not.toBeInTheDocument();
  });

});
