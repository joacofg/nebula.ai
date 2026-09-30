import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ApiKeyTable } from "@/components/api-keys/api-key-table";
import { renderWithProviders } from "@/test/render";

describe("api-keys-page api-key-table", () => {
  it("shows when a single tenant is inferred automatically", () => {
    renderWithProviders(
      <ApiKeyTable
        apiKeys={[
          {
            id: "key-1",
            name: "Tenant Key",
            key_prefix: "nbk_1234",
            tenant_id: null,
            allowed_tenant_ids: ["tenant-a"],
            revoked_at: null,
            created_at: "2026-03-16T12:00:00Z",
            updated_at: "2026-03-16T12:00:00Z",
          },
        ]}
        onRevoke={vi.fn()}
        revokingId={null}
      />,
    );

    expect(screen.getByText("Único tenant: tenant-a")).toBeInTheDocument();
    expect(
      screen.getByTitle(/El header X-Nebula-Tenant-ID es opcional/i),
    ).toBeInTheDocument();
  });

  it("shows when multiple tenants require the tenant header", () => {
    renderWithProviders(
      <ApiKeyTable
        apiKeys={[
          {
            id: "key-2",
            name: "Shared Key",
            key_prefix: "nbk_5678",
            tenant_id: null,
            allowed_tenant_ids: ["tenant-a", "tenant-b"],
            revoked_at: null,
            created_at: "2026-03-16T12:00:00Z",
            updated_at: "2026-03-16T12:00:00Z",
          },
        ]}
        onRevoke={vi.fn()}
        revokingId={null}
      />,
    );

    expect(screen.getByText("2 tenants permitidos")).toBeInTheDocument();
    expect(
      screen.getByTitle(/Los pedidos tienen que enviar X-Nebula-Tenant-ID/i),
    ).toBeInTheDocument();
  });

  it("keeps revoked records visible", () => {
    renderWithProviders(
      <ApiKeyTable
        apiKeys={[
          {
            id: "key-3",
            name: "Tenant Key",
            key_prefix: "nbk_1234",
            tenant_id: "tenant-a",
            allowed_tenant_ids: ["tenant-a"],
            revoked_at: "2026-03-16T12:00:00Z",
            created_at: "2026-03-16T12:00:00Z",
            updated_at: "2026-03-16T12:00:00Z",
          },
        ]}
        onRevoke={vi.fn()}
        revokingId={null}
      />,
    );

    expect(screen.getByText("revocada")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Revocar" })).toBeDisabled();
    expect(screen.getByText("Por defecto: tenant-a")).toBeInTheDocument();
  });
});
