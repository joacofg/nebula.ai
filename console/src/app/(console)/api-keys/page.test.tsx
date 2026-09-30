import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/admin-session-provider", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/admin-session-provider")>();
  return { ...actual, useAdminSession: vi.fn() };
});

vi.mock("@/lib/admin-api", () => ({
  ADMIN_API_KEYS_ENDPOINT: "/v1/admin/api-keys",
  createApiKey: vi.fn(),
  listApiKeys: vi.fn(),
  listTenants: vi.fn(),
  revokeApiKey: vi.fn(),
}));

import ApiKeysPage from "@/app/(console)/api-keys/page";
import { listApiKeys, listTenants, revokeApiKey } from "@/lib/admin-api";
import { useAdminSession } from "@/lib/admin-session-provider";
import { renderWithProviders } from "@/test/render";

beforeEach(() => {
  vi.mocked(useAdminSession).mockReturnValue({
    adminKey: "admin-key",
    isAuthenticated: true,
    isSigningIn: false,
    signIn: vi.fn().mockResolvedValue(undefined),
    signOut: vi.fn(),
    clearSession: vi.fn(),
  });
  vi.mocked(listTenants).mockResolvedValue([]);
  vi.mocked(listApiKeys).mockResolvedValue([
    {
      id: "key-1",
      name: "Support bot",
      key_prefix: "nbk_sup",
      tenant_id: "tenant-a",
      allowed_tenant_ids: ["tenant-a"],
      revoked_at: null,
      created_at: "2026-09-30T12:00:00Z",
      updated_at: "2026-09-30T12:00:00Z",
    },
  ]);
  vi.mocked(revokeApiKey).mockReset().mockResolvedValue(undefined as never);
});

describe("api keys page", () => {
  it("titles the page and offers to create a key", async () => {
    renderWithProviders(<ApiKeysPage />);
    expect(await screen.findByRole("heading", { level: 1, name: "Claves de API" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Crear clave" })).toBeInTheDocument();
  });

  it("shows the error when the key list fails", async () => {
    vi.mocked(listApiKeys).mockRejectedValue(new Error("Keys unavailable."));
    renderWithProviders(<ApiKeysPage />);
    expect(await screen.findByText("Keys unavailable.")).toBeInTheDocument();
  });
});

describe("api keys page revoke flow", () => {
  it("asks for confirmation in an alert dialog and revokes on confirm", async () => {
    const confirmSpy = vi.spyOn(window, "confirm");
    const user = userEvent.setup();
    renderWithProviders(<ApiKeysPage />);

    await user.click(await screen.findByRole("button", { name: /Revocar/ }));
    const dialog = await screen.findByRole("alertdialog");
    expect(within(dialog).getByText(/Support bot/)).toBeInTheDocument();
    expect(confirmSpy).not.toHaveBeenCalled();

    await user.click(within(dialog).getByRole("button", { name: "Revocar clave" }));
    await waitFor(() => expect(revokeApiKey).toHaveBeenCalledWith("admin-key", "key-1"));
  });

  it("does not revoke when the dialog is cancelled", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ApiKeysPage />);

    await user.click(await screen.findByRole("button", { name: /Revocar/ }));
    const dialog = await screen.findByRole("alertdialog");
    await user.click(within(dialog).getByRole("button", { name: "Cancelar" }));

    await waitFor(() => expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument());
    expect(revokeApiKey).not.toHaveBeenCalled();
  });
});
