import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FrontierChart } from "@/components/evaluation/frontier-chart";
import { paretoFront, randomFrontier, type ReplayBaselines } from "@/lib/router-replay";
import { routerReplayFixture } from "@/test/router-replay-fixture";

function numericAttributes(container: HTMLElement) {
  const values: string[] = [];
  container.querySelectorAll("svg *").forEach((node) => {
    for (const name of ["x", "y", "x1", "x2", "y1", "y2", "cx", "cy", "r", "d", "points", "width", "height"]) {
      const value = node.getAttribute(name);
      if (value !== null) {
        values.push(value);
      }
    }
  });
  return values;
}

describe("FrontierChart", () => {
  it("draws the router curve, the random mix and every reference marker", () => {
    render(
      <FrontierChart
        front={paretoFront(routerReplayFixture.operating_points)}
        random={randomFrontier(routerReplayFixture.baselines)}
        baselines={routerReplayFixture.baselines}
        current={{ cost: 0.0025, quality: 1 }}
      />,
    );

    expect(screen.getByRole("group", { name: /Frontera costo–calidad/ })).toBeInTheDocument();
    for (const label of ["todo local", "todo economy", "todo frontier", "heurística v0 (base)", "oráculo", "punto elegido"]) {
      expect(screen.getAllByText(label).length).toBeGreaterThan(0);
    }
    expect(screen.getByText("Costo · USD / 1000 pedidos")).toBeInTheDocument();
    expect(screen.getByText("Calidad")).toBeInTheDocument();
    expect(screen.getByTestId("router-curve")).toBeInTheDocument();
    expect(screen.getByTestId("random-mix")).toBeInTheDocument();
  });

  it("keeps every coordinate finite with zero or one Pareto points and zero costs", () => {
    const flat: ReplayBaselines = {
      all_local: { cost: 0, quality: 1 },
      all_economy: { cost: 0, quality: 1 },
      all_frontier: { cost: 0, quality: 1 },
      oracle: { cost: 0, quality: 1 },
      heuristic_premium_frontier: { cost: 0, quality: 1 },
      heuristic_premium_economy: { cost: 0, quality: 1 },
    };
    for (const front of [[], [{ tau_local: 0, tau_economy: 0, quality: 1, cost_per_prompt: 0 }]]) {
      const { container, unmount } = render(
        <FrontierChart front={front} random={randomFrontier(flat)} baselines={flat} current={{ cost: 0, quality: 1 }} />,
      );
      const values = numericAttributes(container);
      expect(values.length).toBeGreaterThan(0);
      for (const value of values) {
        expect(value).not.toMatch(/NaN|Infinity/);
      }
      unmount();
    }
  });

  it("offers the plotted values as a table", () => {
    render(
      <FrontierChart
        front={paretoFront(routerReplayFixture.operating_points)}
        random={randomFrontier(routerReplayFixture.baselines)}
        baselines={routerReplayFixture.baselines}
        current={{ cost: 0.0025, quality: 1 }}
      />,
    );

    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Ver tabla" }));
    const table = screen.getByRole("table", { name: "Valores del gráfico" });
    expect(table).toHaveTextContent("todo frontier");
    expect(within(table).getByRole("columnheader", { name: "Costo por 1000 pedidos" })).toBeInTheDocument();
    expect(within(table).getByRole("row", { name: /todo frontier/ })).toHaveTextContent("USD 4.000");
    expect(table).not.toHaveTextContent("$");
  });

  it("tells assistive technology whether the table is open", () => {
    render(
      <FrontierChart
        front={paretoFront(routerReplayFixture.operating_points)}
        random={randomFrontier(routerReplayFixture.baselines)}
        baselines={routerReplayFixture.baselines}
        current={{ cost: 0.0025, quality: 1 }}
      />,
    );

    const toggle = screen.getByRole("button", { name: "Ver tabla" });
    expect(toggle).toHaveAttribute("aria-expanded", "false");

    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("table", { name: "Valores del gráfico" })).toBeInTheDocument();

    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("writes every cost as USD, never with a dollar sign", () => {
    render(
      <FrontierChart
        front={paretoFront(routerReplayFixture.operating_points)}
        random={randomFrontier(routerReplayFixture.baselines)}
        baselines={routerReplayFixture.baselines}
        current={{ cost: 0.0025, quality: 1 }}
      />,
    );

    expect(
      screen.getByRole("group", { name: /punto elegido USD 2\.50 por 1000 pedidos, calidad 1\.000/ }),
    ).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "todo frontier: USD 4.000 / 1000 · calidad 1.000" })).toBeInTheDocument();
  });
});
