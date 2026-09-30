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

    expect(screen.getByText("0 / 4 prompts")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Paso" }));

    expect(screen.getByText("1 / 4 prompts")).toBeInTheDocument();
    const [first] = feedItems();
    expect(within(first).getByText("local")).toBeInTheDocument();
    expect(within(first).getByLabelText("suficiente")).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Calidad acumulada" })).toHaveTextContent("1.000");
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
    expect(screen.getByRole("group", { name: "Costo acumulado" })).toHaveTextContent("$2.000");
  });

  it("plays at the chosen speed, stops at the end and cleans up on unmount", () => {
    vi.useFakeTimers();
    const { unmount } = render(<ReplayFeed rows={rows} order={order} point={cheap} initialPlaying />);

    fireEvent.click(screen.getByRole("button", { name: "10×" }));
    act(() => {
      vi.advanceTimersByTime(250);
    });
    expect(screen.getByText("2 / 4 prompts")).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(2000);
    });
    expect(screen.getByText("4 / 4 prompts")).toBeInTheDocument();
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
    expect(screen.getByText("0 / 4 prompts")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Reanudar" }));
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(screen.getByText("1 / 4 prompts")).toBeInTheDocument();
  });
});
