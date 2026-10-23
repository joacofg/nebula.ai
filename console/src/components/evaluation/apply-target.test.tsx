import { screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApplyTarget } from "@/components/evaluation/apply-target";
import { useTenantTarget } from "@/components/evaluation/use-tenant-target";
import { renderWithProviders } from "@/test/render";

const adminApi = vi.hoisted(() => ({
  listTenants: vi.fn(),
  getTenantPolicy: vi.fn(),
  updateTenantPolicy: vi.fn(),
}));

vi.mock("@/lib/admin-api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/admin-api")>("@/lib/admin-api");
  return { ...actual, ...adminApi };
});

function Harness() {
  const tenantTarget = useTenantTarget("nebula-admin-key");
  return <ApplyTarget adminKey="nebula-admin-key" tenantTarget={tenantTarget} />;
}

describe("ApplyTarget", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("says there are no tenants and offers nothing to apply to", async () => {
    adminApi.listTenants.mockResolvedValue([]);
    renderWithProviders(<Harness />, { adminKey: "nebula-admin-key" });

    await waitFor(() => expect(adminApi.listTenants).toHaveBeenCalled());
    expect(await screen.findByRole("option", { name: "Sin tenants" })).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Tenant" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Aplicar al tenant" })).toBeDisabled();
    expect(screen.queryByText(/Objetivo actual/)).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Probar en Playground" })).not.toBeInTheDocument();
    expect(adminApi.getTenantPolicy).not.toHaveBeenCalled();
  });
});
