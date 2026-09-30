import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Figure } from "@/components/system/figure";
import { PageHeader } from "@/components/system/page-header";
import { Readout } from "@/components/system/readout";
import { EmptyState, ErrorAlert, LoadingRows } from "@/components/system/state";
import { TierBadge } from "@/components/system/tier-badge";

describe("TierBadge", () => {
  it.each([
    ["local", "local"],
    ["economy", "economy"],
    ["frontier", "frontier"],
    ["cache", "caché"],
    ["denied", "denegado"],
    ["x-custom", "x-custom"],
  ])("labels %s as %s", (tier, label) => {
    render(<TierBadge tier={tier} />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });
});

describe("ErrorAlert", () => {
  it("shows the error message", () => {
    render(<ErrorAlert error={new Error("boom")} fallback="No se pudo cargar." />);
    expect(screen.getByRole("alert")).toHaveTextContent("boom");
  });

  it("falls back when the error is not an Error", () => {
    render(<ErrorAlert error="nope" fallback="No se pudo cargar." />);
    expect(screen.getByRole("alert")).toHaveTextContent("No se pudo cargar.");
  });
});

describe("EmptyState and LoadingRows", () => {
  it("renders the title and the action", () => {
    render(<EmptyState title="No hay pedidos en este rango." action={<button type="button">Abrir Playground</button>} />);
    expect(screen.getByText("No hay pedidos en este rango.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Abrir Playground" })).toBeInTheDocument();
  });

  it("announces loading with the requested number of rows", () => {
    render(<LoadingRows rows={3} label="Cargando pedidos" />);
    const status = screen.getByRole("status", { name: "Cargando pedidos" });
    expect(status.querySelectorAll("[data-slot=skeleton]")).toHaveLength(3);
  });
});

describe("Figure", () => {
  it("numbers the caption", () => {
    render(
      <Figure number={1} caption="Calidad en función del costo.">
        <svg />
      </Figure>,
    );
    const figure = screen.getByRole("figure");
    expect(within(figure).getByText("Figura 1.")).toBeInTheDocument();
    expect(within(figure).getByText("Calidad en función del costo.")).toBeInTheDocument();
  });
});

describe("PageHeader", () => {
  it("renders the title as h1 and each cell with its label", () => {
    render(
      <PageHeader
        title="Evaluación del router"
        cells={[
          { label: "Router", value: "v1 · 3 niveles" },
          { label: "Corpus", value: "1250 pedidos" },
        ]}
        actions={<button type="button">Aplicar</button>}
      />,
    );
    expect(screen.getByRole("heading", { level: 1, name: "Evaluación del router" })).toBeInTheDocument();
    expect(screen.getByText("Router")).toBeInTheDocument();
    expect(screen.getByText("v1 · 3 niveles")).toBeInTheDocument();
    expect(screen.getByText("1250 pedidos")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Aplicar" })).toBeInTheDocument();
  });
});

describe("Readout", () => {
  it("pairs each label with its value", () => {
    render(
      <Readout
        items={[
          { label: "Costo por 1000 pedidos", value: "USD 1.70", emphasis: true },
          { label: "Calidad", value: "0.957" },
        ]}
      />,
    );
    const term = screen.getByText("Costo por 1000 pedidos");
    expect(term.tagName).toBe("DT");
    expect(term.nextElementSibling).toHaveTextContent("USD 1.70");
    expect(screen.getByText("0.957").tagName).toBe("DD");
  });
});
