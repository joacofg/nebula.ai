import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DecisionPath } from "@/components/system/decision-path";

function mockReducedMotion(reduce: boolean) {
  vi.stubGlobal(
    "matchMedia",
    vi.fn().mockImplementation((query: string) => ({
      matches: reduce && query.includes("prefers-reduced-motion"),
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("DecisionPath", () => {
  it("describes a local rejection followed by economy", () => {
    render(
      <DecisionPath
        steps={[
          { tier: "local", p: 0.41, tau: 0.82 },
          { tier: "economy", p: 0.95, tau: 0.92 },
        ]}
        chosen="economy"
      />,
    );
    const img = screen.getByRole("img");
    expect(img).toHaveAccessibleName("Decisión: local descartado (p 0.41 < τ 0.82), economy elegido (p 0.95 ≥ τ 0.92)");
    expect(img.querySelector("[data-chosen=true]")).toHaveTextContent("economy");
    expect(img.querySelectorAll("a, button, [tabindex]")).toHaveLength(0);
  });

  it("ends in frontier when both steps fall short", () => {
    render(
      <DecisionPath
        steps={[
          { tier: "local", p: 0.3, tau: 0.82 },
          { tier: "economy", p: 0.5, tau: 0.92 },
        ]}
        chosen="frontier"
      />,
    );
    expect(screen.getByRole("img")).toHaveAccessibleName(
      "Decisión: local descartado (p 0.30 < τ 0.82), economy descartado (p 0.50 < τ 0.92), frontier elegido",
    );
  });

  it("stops at local when the first step clears", () => {
    render(<DecisionPath steps={[{ tier: "local", p: 0.9, tau: 0.82 }]} chosen="local" />);
    expect(screen.getByRole("img")).toHaveAccessibleName("Decisión: local elegido (p 0.90 ≥ τ 0.82)");
  });

  it("says when a probability was not recorded or a threshold is infinite", () => {
    render(
      <DecisionPath
        steps={[
          { tier: "local", p: null, tau: 0.82 },
          { tier: "economy", p: 0.95, tau: null },
        ]}
        chosen="frontier"
      />,
    );
    expect(screen.getByRole("img")).toHaveAccessibleName(
      "Decisión: local sin dato (p sin dato · τ 0.82), economy descartado (p 0.95 < τ ∞), frontier elegido",
    );
    expect(screen.getByText("p sin dato · τ 0.82")).toBeInTheDocument();
    expect(screen.getByText("p 0.95 < τ ∞")).toBeInTheDocument();
  });

  it("traces the path when animated and motion is allowed", () => {
    mockReducedMotion(false);
    render(<DecisionPath steps={[{ tier: "local", p: 0.9, tau: 0.82 }]} chosen="local" animate />);
    expect(screen.getByRole("img").querySelectorAll(".decision-trace").length).toBeGreaterThan(0);
  });

  it("stays static with reduced motion", () => {
    mockReducedMotion(true);
    render(<DecisionPath steps={[{ tier: "local", p: 0.9, tau: 0.82 }]} chosen="local" animate />);
    expect(screen.getByRole("img").querySelectorAll(".decision-trace")).toHaveLength(0);
  });

  it("draws every tier even when local wins, with the untried stages marked as not evaluated", () => {
    render(
      <DecisionPath
        steps={[
          { tier: "local", p: 0.9, tau: 0.82 },
          { tier: "economy", p: 0.4, tau: 0.92 },
        ]}
        chosen="local"
      />,
    );
    const img = screen.getByRole("img");
    expect(img).toHaveAccessibleName("Decisión: local elegido (p 0.90 ≥ τ 0.82)");
    expect(img.querySelector('[data-stage="economy"]')).toHaveAttribute("data-evaluated", "false");
    expect(img.querySelector('[data-stage="frontier"]')).toHaveAttribute("data-evaluated", "false");
    expect(img.querySelector("[data-chosen=true]")).toHaveTextContent("local");
    // The router never compared economy: no comparison is drawn for it, so none can read as a result.
    expect(img.querySelector('[data-stage="economy"]')).toHaveTextContent("no evaluado");
    expect(screen.queryByText(/τ 0\.92/)).not.toBeInTheDocument();
  });

  it("writes each evaluated node's comparison as text", () => {
    render(
      <DecisionPath
        steps={[
          { tier: "local", p: 0.41, tau: 0.82 },
          { tier: "economy", p: 0.95, tau: 0.92 },
        ]}
        chosen="economy"
      />,
    );
    const img = screen.getByRole("img");
    expect(img.querySelector('[data-stage="local"]')).toHaveTextContent("p 0.41 < τ 0.82");
    expect(img.querySelector('[data-stage="economy"]')).toHaveTextContent("p 0.95 ≥ τ 0.92");
  });

  it("writes the comparison of a step that clears as p ≥ τ", () => {
    render(<DecisionPath steps={[{ tier: "local", p: 0.82, tau: 0.75 }]} chosen="local" />);
    expect(screen.getByText("p 0.82 ≥ τ 0.75")).toBeInTheDocument();
  });

  it("keeps a probability's four decimals in the comparison", () => {
    render(<DecisionPath steps={[{ tier: "local", p: 0.8312, tau: 0.8234 }]} chosen="local" />);
    expect(screen.getByText("p 0.8312 ≥ τ 0.8234")).toBeInTheDocument();
  });

  it("adds decimals, up to six, until p and τ read differently, so a comparison never contradicts its own text", () => {
    // Both round to 0.8215 at four decimals: "p 0.8215 < τ 0.8215" would read as false.
    render(
      <DecisionPath
        steps={[
          { tier: "local", p: 0.82149, tau: 0.82151 },
          { tier: "economy", p: 0.95, tau: 0.92 },
        ]}
        chosen="economy"
      />,
    );
    const img = screen.getByRole("img");
    expect(img.querySelector('[data-stage="local"]')).toHaveTextContent("p 0.82149 < τ 0.82151");
    expect(img).toHaveAccessibleName(
      "Decisión: local descartado (p 0.82149 < τ 0.82151), economy elegido (p 0.95 ≥ τ 0.92)",
    );
    expect(img.textContent).not.toContain("p 0.8215 <");
  });

  it("does the same when p is the one just above τ", () => {
    render(<DecisionPath steps={[{ tier: "local", p: 0.82151, tau: 0.82149 }]} chosen="local" />);
    expect(screen.getByText("p 0.82151 ≥ τ 0.82149")).toBeInTheDocument();
    expect(screen.getByRole("img")).toHaveAccessibleName("Decisión: local elegido (p 0.82151 ≥ τ 0.82149)");
  });

  it("leaves a probability equal to its threshold at two decimals", () => {
    render(<DecisionPath steps={[{ tier: "local", p: 0.82, tau: 0.82 }]} chosen="local" />);
    expect(screen.getByText("p 0.82 ≥ τ 0.82")).toBeInTheDocument();
  });

  it.each([
    ["local wins", [{ tier: "local", p: 0.9, tau: 0.82 }, { tier: "economy", p: 0.4, tau: 0.92 }], "local"],
    ["economy wins", [{ tier: "local", p: 0.41, tau: 0.82 }, { tier: "economy", p: 0.95, tau: 0.92 }], "economy"],
    ["frontier wins", [{ tier: "local", p: 0.3, tau: 0.82 }, { tier: "economy", p: 0.5, tau: 0.92 }], "frontier"],
    ["it is served from the cache", [], "cache"],
  ] as const)("never fades a branch with opacity when %s", (_name, steps, chosen) => {
    render(<DecisionPath steps={[...steps]} chosen={chosen} animate />);
    expect(screen.getByRole("img").querySelectorAll('[class*="opacity-"]')).toHaveLength(0);
  });

  // The branches of the cascade: "local-exit" and "economy-exit" lead to a tier's terminal,
  // "to-economy" and "to-frontier" lead on to the next stage.
  it.each([
    [
      "local wins",
      [{ tier: "local", p: 0.9, tau: 0.82 }, { tier: "economy", p: 0.4, tau: 0.92 }],
      "local",
      ["economy-exit", "to-economy", "to-frontier"],
    ],
    [
      "economy wins",
      [{ tier: "local", p: 0.41, tau: 0.82 }, { tier: "economy", p: 0.95, tau: 0.92 }],
      "economy",
      ["local-exit", "to-frontier"],
    ],
    [
      "frontier wins",
      [{ tier: "local", p: 0.3, tau: 0.82 }, { tier: "economy", p: 0.5, tau: 0.92 }],
      "frontier",
      ["economy-exit", "local-exit"],
    ],
  ] as const)("dashes exactly the branches not taken when %s, and keeps the one taken solid", (_name, steps, chosen, dashedBranches) => {
    render(<DecisionPath steps={[...steps]} chosen={chosen} />);
    const img = screen.getByRole("img");

    const dashed = [...img.querySelectorAll("path[stroke-dasharray]")].map((path) => path.getAttribute("data-branch"));
    expect(dashed.sort()).toEqual([...dashedBranches].sort());

    const taken = img.querySelector('path[data-branch="taken"]')!;
    expect(taken).not.toHaveAttribute("stroke-dasharray");
  });

  it("draws the comparison in the sans label face, not the mono one that lacks Greek", () => {
    render(<DecisionPath steps={[{ tier: "local", p: 0.41, tau: 0.82 }, { tier: "economy", p: 0.95, tau: 0.92 }]} chosen="economy" />);
    const comparisons = [...screen.getByRole("img").querySelectorAll("text")].filter((t) => t.textContent?.includes("τ"));
    expect(comparisons).toHaveLength(2);
    for (const comparison of comparisons) {
      expect(comparison).toHaveClass("font-label");
      expect(comparison).not.toHaveClass("font-mono");
    }
  });

  it("renders the compact layout at its drawn size", () => {
    render(
      <DecisionPath
        compact
        steps={[
          { tier: "local", p: 0.41, tau: 0.82 },
          { tier: "economy", p: 0.95, tau: 0.92 },
        ]}
        chosen="economy"
      />,
    );
    const img = screen.getByRole("img");
    const [, , viewWidth] = (img.getAttribute("viewBox") ?? "").split(" ").map(Number);
    expect(Number(img.getAttribute("width"))).toBe(viewWidth);
    expect(viewWidth).toBeLessThanOrEqual(352);
    expect(img).toHaveAccessibleName("Decisión: local descartado (p 0.41 < τ 0.82), economy elegido (p 0.95 ≥ τ 0.92)");
  });
});

