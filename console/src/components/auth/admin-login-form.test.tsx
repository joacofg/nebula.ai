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

  it("tells a wrong key apart: 401 shows the invalid-key message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Missing or invalid admin API key." }), { status: 401 }),
      ),
    );

    renderWithProviders(<AdminLoginForm reason="session-expired" />);

    expect(screen.getByText("La sesión se cerró. Ingresar la clave de admin otra vez.")).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText("Clave de admin"), "bad-key");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByText("La clave de admin no es válida.")).toBeInTheDocument();
    expect(screen.queryByText("Missing or invalid admin API key.")).not.toBeInTheDocument();
  });

  it("tells a gateway that is down apart from a wrong key", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "gateway_unreachable" }), { status: 503 })),
    );

    renderWithProviders(<AdminLoginForm />);

    await userEvent.type(screen.getByLabelText("Clave de admin"), "valid-admin-key");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByText("No se pudo conectar con el gateway.")).toBeInTheDocument();
    expect(screen.queryByText("La clave de admin no es válida.")).not.toBeInTheDocument();
  });

  it("shows the unreachable message when the console server itself does not answer", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    renderWithProviders(<AdminLoginForm />);

    await userEvent.type(screen.getByLabelText("Clave de admin"), "valid-admin-key");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByText("No se pudo conectar con el gateway.")).toBeInTheDocument();
  });
});
