import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AdminLoginForm } from "@/components/auth/admin-login-form";
import { renderWithProviders } from "@/test/render";

const replace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace,
  }),
}));

describe("AdminLoginForm", () => {
  beforeEach(() => {
    replace.mockReset();
    vi.restoreAllMocks();
  });

  it("requires the Nebula admin key on blur", async () => {
    renderWithProviders(<AdminLoginForm />);

    const input = screen.getByLabelText("Nebula admin key");
    await userEvent.click(input);
    await userEvent.tab();

    expect(screen.getByRole("alert")).toHaveTextContent("Nebula admin key is required.");
  });

  it("signs in and routes to tenants", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: "ok" }),
      }),
    );

    renderWithProviders(<AdminLoginForm />);

    await userEvent.type(screen.getByLabelText("Nebula admin key"), "valid-admin-key");
    await userEvent.click(screen.getByRole("button", { name: "Enter console" }));

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/tenants"));
  });

  it("renders backend validation errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({ detail: "Missing or invalid admin API key." }),
      }),
    );

    renderWithProviders(<AdminLoginForm reason="session-expired" />);

    expect(screen.getByText(/Enter the Nebula admin key again/)).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText("Nebula admin key"), "bad-key");
    await userEvent.click(screen.getByRole("button", { name: "Enter console" }));

    await waitFor(() => {
      expect(screen.getByText("Missing or invalid admin API key.")).toBeInTheDocument();
    });
  });
});
