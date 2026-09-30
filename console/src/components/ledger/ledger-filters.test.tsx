import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { LedgerFilters } from "@/components/ledger/ledger-filters";
import { renderWithProviders } from "@/test/render";

describe("ledger-filters", () => {
  it("renders the expected filter controls and refresh action", async () => {
    const user = userEvent.setup();
    const onRefresh = vi.fn();

    renderWithProviders(
      <LedgerFilters
        tenants={[
          {
            id: "default",
            name: "Default Workspace",
            description: "Bootstrap tenant",
            metadata: {},
            active: true,
            created_at: "2026-03-16T12:00:00Z",
            updated_at: "2026-03-16T12:00:00Z",
          },
        ]}
        tenantId=""
        routeTarget=""
        terminalStatus=""
        fromTimestamp=""
        toTimestamp=""
        onTenantIdChange={vi.fn()}
        onRouteTargetChange={vi.fn()}
        onTerminalStatusChange={vi.fn()}
        onFromTimestampChange={vi.fn()}
        onToTimestampChange={vi.fn()}
        onRefresh={onRefresh}
      />,
    );

    for (const name of ["Tenant", "Ruta", "Estado", "Desde", "Hasta"]) {
      expect(screen.getByLabelText(name)).toBeInTheDocument();
    }
    expect(screen.getByRole("option", { name: "Todos los tenants" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "embeddings" })).toBeInTheDocument();
    // Options read in Spanish, like the ledger rows; the values stay the gateway's codes.
    const route = within(screen.getByRole("combobox", { name: "Ruta" }));
    const status = within(screen.getByRole("combobox", { name: "Estado" }));
    expect(route.getByRole("option", { name: "caché" })).toHaveValue("cache");
    expect(route.getByRole("option", { name: "denegado" })).toHaveValue("denied");
    expect(status.getByRole("option", { name: "caché" })).toHaveValue("cache_hit");
    expect(status.getByRole("option", { name: "completado" })).toHaveValue("completed");
    expect(status.getByRole("option", { name: "error del proveedor" })).toHaveValue("provider_error");

    await user.click(screen.getByRole("button", { name: "Actualizar" }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });

  it("uses the existing route target callback when embeddings is selected", async () => {
    const user = userEvent.setup();
    const onRouteTargetChange = vi.fn();

    const filters = (routeTarget: string) => (
      <LedgerFilters
        tenants={[]}
        tenantId=""
        routeTarget={routeTarget}
        terminalStatus=""
        fromTimestamp=""
        toTimestamp=""
        onTenantIdChange={vi.fn()}
        onRouteTargetChange={onRouteTargetChange}
        onTerminalStatusChange={vi.fn()}
        onFromTimestampChange={vi.fn()}
        onToTimestampChange={vi.fn()}
        onRefresh={vi.fn()}
      />
    );

    const { rerender } = renderWithProviders(filters(""));

    await user.selectOptions(screen.getByRole("combobox", { name: "Ruta" }), "embeddings");

    expect(onRouteTargetChange).toHaveBeenCalledWith("embeddings");
    // The select is controlled by the routeTarget prop, so picking an option does
    // not move it on its own; the parent owns the value and passes it back down.
    expect(screen.getByRole("combobox", { name: "Ruta" })).toHaveValue("");

    rerender(filters("embeddings"));
    expect(screen.getByRole("combobox", { name: "Ruta" })).toHaveValue("embeddings");
  });
});
