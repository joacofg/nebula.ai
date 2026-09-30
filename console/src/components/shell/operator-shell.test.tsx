import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const push = vi.fn();
let pathname = "/evaluacion";

vi.mock("next/navigation", () => ({
  usePathname: () => pathname,
  useRouter: () => ({ push, replace: vi.fn() }),
}));

vi.mock("@/lib/admin-session-provider", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/admin-session-provider")>();
  return { ...actual, useAdminSession: vi.fn() };
});

import { OperatorShell } from "@/components/shell/operator-shell";
import { useAdminSession } from "@/lib/admin-session-provider";
import { renderWithProviders } from "@/test/render";

const signOut = vi.fn();

beforeEach(() => {
  push.mockReset();
  signOut.mockReset();
  pathname = "/evaluacion";
  vi.mocked(useAdminSession).mockReturnValue({
    adminKey: "admin-key",
    isAuthenticated: true,
    isSigningIn: false,
    signIn: vi.fn(),
    signOut,
    clearSession: vi.fn(),
  });
});

describe("OperatorShell", () => {
  it("groups the six pages under Operar and Configurar", () => {
    renderWithProviders(<OperatorShell>contenido</OperatorShell>);
    const nav = screen.getByRole("navigation", { name: "Principal" });
    expect(within(nav).getByText("Operar")).toBeInTheDocument();
    expect(within(nav).getByText("Configurar")).toBeInTheDocument();
    const names = within(nav)
      .getAllByRole("link")
      .map((link) => link.textContent?.trim());
    expect(names).toEqual(["Evaluación", "Playground", "Observabilidad", "Tenants", "Claves de API", "Política"]);
  });

  it("marks the current page", () => {
    pathname = "/observability";
    renderWithProviders(<OperatorShell>contenido</OperatorShell>);
    expect(screen.getByRole("link", { name: "Observabilidad" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Evaluación" })).not.toHaveAttribute("aria-current");
  });

  it("signs out and returns to the login", async () => {
    renderWithProviders(<OperatorShell>contenido</OperatorShell>);
    await userEvent.click(screen.getByRole("button", { name: "Cerrar sesión" }));
    expect(signOut).toHaveBeenCalled();
    expect(push).toHaveBeenCalledWith("/?reason=signed_out");
  });

  it("renders the page inside the main landmark", () => {
    renderWithProviders(<OperatorShell>contenido</OperatorShell>);
    expect(screen.getByRole("main")).toHaveTextContent("contenido");
  });
});
