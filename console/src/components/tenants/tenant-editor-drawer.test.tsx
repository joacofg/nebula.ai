import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TenantEditorDrawer } from "@/components/tenants/tenant-editor-drawer";
import { renderWithProviders } from "@/test/render";

describe("tenant-editor-drawer", () => {
  it("keeps id readOnly during edit", () => {
    renderWithProviders(
      <TenantEditorDrawer
        mode="edit"
        tenant={{
          id: "tenant-a",
          name: "Tenant A",
          description: "Primary",
          metadata: { tier: "gold" },
          active: true,
          created_at: "2026-03-16T12:00:00Z",
          updated_at: "2026-03-16T12:00:00Z",
        }}
        isSaving={false}
        onClose={vi.fn()}
        onSubmit={vi.fn().mockResolvedValue(undefined)}
      />,
    );

    expect(screen.getByLabelText("id")).toHaveAttribute("readonly");
  });

  it("validates metadata JSON before submit", async () => {
    renderWithProviders(
      <TenantEditorDrawer
        mode="create"
        tenant={null}
        isSaving={false}
        onClose={vi.fn()}
        onSubmit={vi.fn().mockResolvedValue(undefined)}
      />,
    );

    await userEvent.type(screen.getByLabelText("id"), "new-team");
    await userEvent.type(screen.getByLabelText("name"), "New Team");
    await userEvent.clear(screen.getByLabelText("metadata"));
    await userEvent.type(screen.getByLabelText("metadata"), "bad json");
    await userEvent.click(screen.getByRole("button", { name: "Create tenant" }));

    expect(screen.getByText("metadata must be valid JSON.")).toBeInTheDocument();
  });

  it("submits normalized tenant payload", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    renderWithProviders(
      <TenantEditorDrawer
        mode="create"
        tenant={null}
        isSaving={false}
        onClose={vi.fn()}
        onSubmit={onSubmit}
      />,
    );

    await userEvent.type(screen.getByLabelText("id"), "tenant-b");
    await userEvent.type(screen.getByLabelText("name"), "Tenant B");
    await userEvent.click(screen.getByRole("button", { name: "Create tenant" }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          id: "tenant-b",
          name: "Tenant B",
          active: true,
        }),
      );
    });
  });
});
