import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ApiKeyTable } from "@/components/api-keys/api-key-table";
import { renderWithProviders } from "@/test/render";

describe("api-keys-page api-key-table", () => {
  it("keeps revoked records visible", () => {
    renderWithProviders(
      <ApiKeyTable
        apiKeys={[
          {
            id: "key-1",
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
  });
});
