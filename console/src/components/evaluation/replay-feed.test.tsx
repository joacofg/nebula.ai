import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ReplayFeed } from "@/components/evaluation/replay-feed";
import { ALL_FRONTIER } from "@/lib/router-replay";
import { routerReplayFixture } from "@/test/router-replay-fixture";

const rows = routerReplayFixture.rows;
const cheap = routerReplayFixture.operating_points[0];
// Identity order keeps the assertions readable.
const order = [0, 1, 2, 3];

function feedItems() {
  return screen.queryAllByRole("listitem");
}

describe("ReplayFeed", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("routes one prompt per step and keeps running totals", () => {
    render(<ReplayFeed rows={rows} order={order} point={cheap} initialPlaying={false} />);

    expect(screen.getByText("0 / 4 pedidos")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Paso" }));

    expect(screen.getByText("1 / 4 pedidos")).toBeInTheDocument();
    const [first] = feedItems();
    expect(within(first).getByText("local")).toBeInTheDocument();
    expect(within(first).getByLabelText("suficiente")).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Calidad acumulada" })).toHaveTextContent("1.000");
  });

  it("shows no cost or quality before the first prompt, not a zero that contradicts the chart", () => {
    render(<ReplayFeed rows={rows} order={order} point={cheap} initialPlaying={false} />);

    const cost = screen.getByRole("group", { name: "Costo por 1000 pedidos" });
    expect(cost).toHaveTextContent("—");
    expect(cost).toHaveTextContent("promedio hasta ahora");
    expect(screen.getByRole("group", { name: "Calidad acumulada" })).toHaveTextContent("—");
    expect(screen.getByRole("group", { name: "Calidad acumulada" })).not.toHaveTextContent("0.000");

    fireEvent.click(screen.getByRole("button", { name: "Paso" }));

    expect(cost).toHaveTextContent("USD 0.00");
    expect(screen.getByRole("group", { name: "Calidad acumulada" })).toHaveTextContent("1.000");
  });

  it("says the judge ensemble accepted the answers", () => {
    render(<ReplayFeed rows={rows} order={order} point={cheap} initialPlaying={false} />);

    expect(screen.getByRole("group", { name: "Calidad acumulada" })).toHaveTextContent(
      "respuestas aceptadas por el ensamble de jueces",
    );
  });

  it("re-routes from the current prompt when the operating point changes", () => {
    const { rerender } = render(<ReplayFeed rows={rows} order={order} point={cheap} initialPlaying={false} />);
    fireEvent.click(screen.getByRole("button", { name: "Paso" }));

    rerender(<ReplayFeed rows={rows} order={order} point={ALL_FRONTIER} initialPlaying={false} />);
    fireEvent.click(screen.getByRole("button", { name: "Paso" }));

    const items = feedItems();
    // Newest first: the second prompt went to frontier, the first stays local.
    expect(within(items[0]).getByText("frontier")).toBeInTheDocument();
    expect(within(items[1]).getByText("local")).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Costo por 1000 pedidos" })).toHaveTextContent("USD 2.00");
  });

  it("starts at 10×, so the whole corpus replays in about two minutes", () => {
    vi.useFakeTimers();
    render(<ReplayFeed rows={rows} order={order} point={cheap} initialPlaying />);

    expect(screen.getByRole("button", { name: "10×" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "1×" })).toHaveAttribute("aria-pressed", "false");
    act(() => {
      vi.advanceTimersByTime(250);
    });
    expect(screen.getByText("2 / 4 pedidos")).toBeInTheDocument();
  });

  it("plays at the chosen speed, stops at the end and cleans up on unmount", () => {
    vi.useFakeTimers();
    const { unmount } = render(<ReplayFeed rows={rows} order={order} point={cheap} initialPlaying />);

    fireEvent.click(screen.getByRole("button", { name: "1×" }));
    act(() => {
      vi.advanceTimersByTime(2000);
    });
    expect(screen.getByText("2 / 4 pedidos")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "100×" }));
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(screen.getByText("4 / 4 pedidos")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reiniciar" })).toBeInTheDocument();

    unmount();
    expect(vi.getTimerCount()).toBe(0);
  });

  it("pauses and resumes", () => {
    vi.useFakeTimers();
    render(<ReplayFeed rows={rows} order={order} point={cheap} initialPlaying />);

    fireEvent.click(screen.getByRole("button", { name: "Pausar" }));
    act(() => {
      vi.advanceTimersByTime(5000);
    });
    expect(screen.getByText("0 / 4 pedidos")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Reanudar" }));
    act(() => {
      vi.advanceTimersByTime(100);
    });
    expect(screen.getByText("1 / 4 pedidos")).toBeInTheDocument();
  });
});
