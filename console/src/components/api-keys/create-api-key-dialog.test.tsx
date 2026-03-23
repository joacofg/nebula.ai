import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { CreateApiKeyDialog } from "@/components/api-keys/create-api-key-dialog";
import { renderWithProviders } from "@/test/render";

const TENANTS = [
  {
    id: "tenant-a",
    name: "Tenant A",
    description: "Primary",
    metadata: {},
    active: true,
    created_at: "2026-03-16T12:00:00Z",
    updated_at: "2026-03-16T12:00:00Z",
  },
  {
    id: "tenant-b",
    name: "Tenant B",
    description: "Secondary",
    metadata: {},
    active: true,
    created_at: "2026-03-16T12:00:00Z",
    updated_at: "2026-03-16T12:00:00Z",
  },
];

describe("create-api-key-dialog", () => {
  it("explains tenant resolution for multi-tenant keys", () => {
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

    expect(screen.getByText(/Use allowed_tenant_ids to define every tenant the key may access/i)).toBeInTheDocument();
    expect(screen.getByText(/honoring an explicit X-Nebula-Tenant-ID/i)).toBeInTheDocument();
    expect(screen.getByText(/public callers must send the tenant header/i)).toBeInTheDocument();
    expect(screen.getByText(/A single allowed tenant is inferred automatically/i)).toBeInTheDocument();
  });

  it("validates allowed_tenant_ids", async () => {
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

    await userEvent.type(screen.getByLabelText("name"), "Test key");
    await userEvent.click(screen.getByLabelText("Tenant A"));
    await userEvent.click(screen.getByRole("button", { name: "Create API key" }));

    expect(screen.getByText("allowed_tenant_ids must contain at least one tenant.")).toBeInTheDocument();
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

    await userEvent.type(screen.getByLabelText("name"), "Console key");
    await userEvent.click(screen.getByLabelText("Tenant B"));
    await userEvent.click(screen.getByRole("button", { name: "Create API key" }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        name: "Console key",
        tenant_id: "tenant-a",
        allowed_tenant_ids: ["tenant-a", "tenant-b"],
      });
    });
  });
});
