import { screen, within } from "@testing-library/react";
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

    expect(screen.getByRole("columnheader", { name: "Id" })).toBeInTheDocument();
    expect(screen.getByText("activo")).toBeInTheDocument();
    expect(screen.getByText("inactivo")).toBeInTheDocument();
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
  it("reads a zoneless timestamp as UTC, the way SQLite hands it back, and survives one it cannot read", () => {
    renderWithProviders(
      <TenantTable
        tenants={[
          { ...TENANTS[0], id: "zoned", name: "Zoned", updated_at: "2026-03-16T12:30:00Z" },
          { ...TENANTS[0], id: "zoneless", name: "Zoneless", updated_at: "2026-03-16T12:30:00.123456" },
          { ...TENANTS[0], id: "broken", name: "Broken", updated_at: "ayer" },
        ]}
        selectedTenantId={null}
        onSelectTenant={vi.fn()}
      />,
    );

    const updated = (name: string) => {
      const cells = within(screen.getByText(name).closest("tr") as HTMLElement).getAllByRole("cell");
      return cells[cells.length - 1].textContent;
    };
    expect(updated("Zoneless")).toBe(updated("Zoned"));
    expect(updated("Zoned")).toMatch(/\d{1,2}\/\d{1,2}\/\d{2},? \d{2}:\d{2}/);
    expect(updated("Broken")).toBe("ayer");
  });

  it("keeps a long tenant name on one line with the full name in the title", () => {
    const longName = "Laboratorio de Robótica Aplicada del Departamento";
    renderWithProviders(
      <TenantTable
        tenants={[{ ...TENANTS[0], name: longName }]}
        selectedTenantId={null}
        onSelectTenant={vi.fn()}
      />,
    );
    const cell = screen.getByText(longName);
    expect(cell).toHaveAttribute("title", longName);
    expect(cell.className).toContain("truncate");
  });
});
