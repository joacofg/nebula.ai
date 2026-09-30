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
    expect(img).toHaveAccessibleName("Decisión: local descartado (0.41 < 0.82), economy elegido (0.95 ≥ 0.92)");
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
      "Decisión: local descartado (0.30 < 0.82), economy descartado (0.50 < 0.92), frontier elegido",
    );
  });

  it("stops at local when the first step clears", () => {
    render(<DecisionPath steps={[{ tier: "local", p: 0.9, tau: 0.82 }]} chosen="local" />);
    expect(screen.getByRole("img")).toHaveAccessibleName("Decisión: local elegido (0.90 ≥ 0.82)");
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
      "Decisión: local sin dato, economy descartado (0.95 < ∞), frontier elegido",
    );
    expect(screen.getByText("p local sin dato")).toBeInTheDocument();
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
  it("draws every tier even when local wins, with the untried stages faded", () => {
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
    expect(img).toHaveAccessibleName("Decisión: local elegido (0.90 ≥ 0.82)");
    expect(img.querySelector('[data-stage="economy"]')).toHaveAttribute("data-evaluated", "false");
    expect(img.querySelector('[data-stage="frontier"]')).toHaveAttribute("data-evaluated", "false");
    expect(img.querySelector("[data-chosen=true]")).toHaveTextContent("local");
  });
});
