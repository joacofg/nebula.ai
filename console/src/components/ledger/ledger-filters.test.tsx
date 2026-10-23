import type { ComponentProps } from "react";

import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { LedgerFilters } from "@/components/ledger/ledger-filters";
import { renderWithProviders } from "@/test/render";

function filters(overrides: Partial<ComponentProps<typeof LedgerFilters>> = {}) {
  return (
    <LedgerFilters
      tenants={[]}
      tenantId=""
      routeTarget=""
      tier=""
      terminalStatus=""
      fromTimestamp=""
      toTimestamp=""
      onTenantIdChange={vi.fn()}
      onRouteTargetChange={vi.fn()}
      onTierChange={vi.fn()}
      onTerminalStatusChange={vi.fn()}
      onFromTimestampChange={vi.fn()}
      onToTimestampChange={vi.fn()}
      {...overrides}
    />
  );
}

describe("ledger-filters", () => {
  it("renders the expected filter controls", () => {
    renderWithProviders(
      filters({
        tenants: [
          {
            id: "default",
            name: "Default Workspace",
            description: "Bootstrap tenant",
            metadata: {},
            active: true,
            created_at: "2026-03-16T12:00:00Z",
            updated_at: "2026-03-16T12:00:00Z",
          },
        ],
      }),
    );

    for (const name of ["Tenant", "Ruta", "Nivel", "Estado", "Desde", "Hasta"]) {
      expect(screen.getByLabelText(name)).toBeInTheDocument();
    }
    expect(screen.getByRole("option", { name: "Todos los tenants" })).toBeInTheDocument();
    // Options read in Spanish, like the ledger rows; the values stay the gateway's codes.
    const route = within(screen.getByRole("combobox", { name: "Ruta" }));
    const status = within(screen.getByRole("combobox", { name: "Estado" }));
    expect(route.getByRole("option", { name: "Local" })).toHaveValue("local");
    expect(route.getByRole("option", { name: "Premium" })).toHaveValue("premium");
    expect(route.getByRole("option", { name: "Caché" })).toHaveValue("cache");
    expect(route.getByRole("option", { name: "Denegado" })).toHaveValue("denied");
    expect(route.getByRole("option", { name: "Embeddings" })).toHaveValue("embeddings");
    expect(status.getByRole("option", { name: "caché" })).toHaveValue("cache_hit");
    expect(status.getByRole("option", { name: "completado" })).toHaveValue("completed");
    expect(status.getByRole("option", { name: "error del proveedor" })).toHaveValue("provider_error");
    // Refreshing is a page action (the Observabilidad header), not a filter.
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("filters by the tier the router chose, with the options in the thesis order", async () => {
    const user = userEvent.setup();
    const onTierChange = vi.fn();
    renderWithProviders(filters({ onTierChange }));

    const tier = screen.getByRole("combobox", { name: "Nivel" });
    expect(within(tier).getAllByRole("option").map((option) => [option.textContent, (option as HTMLOptionElement).value])).toEqual([
      ["Todos", ""],
      ["local", "local"],
      ["economy", "economy"],
      ["frontier", "frontier"],
    ]);

    await user.selectOptions(tier, "economy");
    expect(onTierChange).toHaveBeenCalledWith("economy");
  });

  it("offers every terminal status the gateway records, the abandoned stream included", async () => {
    const user = userEvent.setup();
    const onTerminalStatusChange = vi.fn();
    renderWithProviders(filters({ onTerminalStatusChange }));

    const status = screen.getByRole("combobox", { name: "Estado" });
    expect(within(status).getByRole("option", { name: "cortado por el cliente" })).toHaveValue("client_disconnected");
    expect(within(status).getByRole("option", { name: "límite de pedidos" })).toHaveValue("rate_limited");
    expect(within(status).getAllByRole("option")).toHaveLength(8);

    await user.selectOptions(status, "client_disconnected");
    expect(onTerminalStatusChange).toHaveBeenCalledWith("client_disconnected");
  });

  it("uses the existing route target callback when embeddings is selected", async () => {
    const user = userEvent.setup();
    const onRouteTargetChange = vi.fn();

    const { rerender } = renderWithProviders(filters({ onRouteTargetChange }));

    await user.selectOptions(screen.getByRole("combobox", { name: "Ruta" }), "embeddings");

    expect(onRouteTargetChange).toHaveBeenCalledWith("embeddings");
    // The select is controlled by the routeTarget prop, so picking an option does
    // not move it on its own; the parent owns the value and passes it back down.
    expect(screen.getByRole("combobox", { name: "Ruta" })).toHaveValue("");

    rerender(filters({ onRouteTargetChange, routeTarget: "embeddings" }));
    expect(screen.getByRole("combobox", { name: "Ruta" })).toHaveValue("embeddings");
  });
});
