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

    expect(screen.getByText("Single allowed tenant: tenant-a")).toBeInTheDocument();
    expect(
      screen.getByText(/Public callers can omit X-Nebula-Tenant-ID because the only authorized tenant is inferred/i),
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

    expect(screen.getByText("2 authorized tenants")).toBeInTheDocument();
    expect(
      screen.getByText(/Public callers must send X-Nebula-Tenant-ID so Nebula can resolve which authorized tenant to use/i),
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

    expect(screen.getByText("Revoked")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Revoke" })).toBeDisabled();
    expect(screen.getByText("Auto-resolves tenant-a")).toBeInTheDocument();
  });
});
