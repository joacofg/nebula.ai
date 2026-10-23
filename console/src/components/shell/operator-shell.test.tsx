import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

let pathname = "/evaluacion";

vi.mock("next/navigation", () => ({
  usePathname: () => pathname,
}));

import { OperatorShell } from "@/components/shell/operator-shell";
import { renderWithProviders } from "@/test/render";

const onSignOut = vi.fn();

function renderShell() {
  return renderWithProviders(<OperatorShell onSignOut={onSignOut}>contenido</OperatorShell>);
}

beforeEach(() => {
  onSignOut.mockReset();
  pathname = "/evaluacion";
});

describe("OperatorShell", () => {
  it("groups the six pages under Operar and Configurar", () => {
    renderShell();
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
    renderShell();
    expect(screen.getByRole("link", { name: "Observabilidad" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Evaluación" })).not.toHaveAttribute("aria-current");
  });

  it("hands signing out to its owner instead of navigating by itself", async () => {
    renderShell();
    await userEvent.click(screen.getByRole("button", { name: "Cerrar sesión" }));
    expect(onSignOut).toHaveBeenCalledTimes(1);
  });

  it("renders the page inside the main landmark", () => {
    renderShell();
    expect(screen.getByRole("main")).toHaveTextContent("contenido");
  });
});
