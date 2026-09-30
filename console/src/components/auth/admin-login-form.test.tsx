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

  it("requires the admin key on blur", async () => {
    renderWithProviders(<AdminLoginForm />);

    const input = screen.getByLabelText("Clave de admin");
    await userEvent.click(input);
    await userEvent.tab();

    expect(screen.getByRole("alert")).toHaveTextContent("Falta la clave de admin.");
  });

  it("signs in and lands on the evaluation page", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: "ok" }),
      }),
    );

    renderWithProviders(<AdminLoginForm />);

    await userEvent.type(screen.getByLabelText("Clave de admin"), "valid-admin-key");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/evaluacion"));
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

    expect(screen.getByText("La sesión se cerró. Ingresar la clave de admin otra vez.")).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText("Clave de admin"), "bad-key");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => {
      expect(screen.getByText("Missing or invalid admin API key.")).toBeInTheDocument();
    });
  });
});
