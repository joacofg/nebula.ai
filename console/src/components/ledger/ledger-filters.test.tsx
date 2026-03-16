import { screen } from "@testing-library/react";
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

    expect(screen.getByText("Tenant")).toBeInTheDocument();
    expect(screen.getByText("Route target")).toBeInTheDocument();
    expect(screen.getByText("Terminal status")).toBeInTheDocument();
    expect(screen.getByText("From")).toBeInTheDocument();
    expect(screen.getByText("To")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Refresh" }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });
});
