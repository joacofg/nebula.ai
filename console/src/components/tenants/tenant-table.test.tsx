import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TenantTable } from "@/components/tenants/tenant-table";
import { renderWithProviders } from "@/test/render";

const TENANTS = [
  {
    id: "active-team",
    name: "Active Team",
    description: "Enabled tenant",
    metadata: {},
    active: true,
    created_at: "2026-03-16T12:00:00Z",
    updated_at: "2026-03-16T12:00:00Z",
  },
  {
    id: "inactive-team",
    name: "Inactive Team",
    description: "Inactive tenant",
    metadata: {},
    active: false,
    created_at: "2026-03-16T12:00:00Z",
    updated_at: "2026-03-16T12:30:00Z",
  },
];

describe("tenants-page tenant-table", () => {
  it("renders active and inactive tenant states", () => {
    renderWithProviders(
      <TenantTable tenants={TENANTS} selectedTenantId={null} onSelectTenant={vi.fn()} />,
    );

    expect(screen.getByText("Tenant ID")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByText("Inactive")).toBeInTheDocument();
  });

  it("does not introduce app or workload pseudo-entity columns", () => {
    renderWithProviders(
      <TenantTable tenants={TENANTS} selectedTenantId={null} onSelectTenant={vi.fn()} />,
    );

    expect(screen.queryByRole("columnheader", { name: /app/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("columnheader", { name: /workload/i })).not.toBeInTheDocument();
  });

  it("selects the chosen tenant row", async () => {
    const onSelectTenant = vi.fn();
    renderWithProviders(
      <TenantTable tenants={TENANTS} selectedTenantId={null} onSelectTenant={onSelectTenant} />,
    );

    await userEvent.click(screen.getByText("Inactive Team"));

    expect(onSelectTenant).toHaveBeenCalledWith(expect.objectContaining({ id: "inactive-team" }));
  });
});
