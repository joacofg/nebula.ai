import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { FreshnessBadge } from "./freshness-badge";

describe("FreshnessBadge", () => {
  it("renders Connected for connected status", () => {
    render(<FreshnessBadge status="connected" />);
    expect(screen.getByText("Connected")).toBeDefined();
  });

  it("renders Degraded for degraded status", () => {
    render(<FreshnessBadge status="degraded" />);
    expect(screen.getByText("Degraded")).toBeDefined();
  });

  it("renders Stale for stale status", () => {
    render(<FreshnessBadge status="stale" />);
    expect(screen.getByText("Stale")).toBeDefined();
  });

  it("renders Offline for offline status", () => {
    render(<FreshnessBadge status="offline" />);
    expect(screen.getByText("Offline")).toBeDefined();
  });

  it("renders Awaiting enrollment for null status (D-14)", () => {
    render(<FreshnessBadge status={null} />);
    expect(screen.getByText("Awaiting enrollment")).toBeDefined();
  });

  it("applies emerald classes for connected", () => {
    const { container } = render(<FreshnessBadge status="connected" />);
    const badge = container.querySelector("span");
    expect(badge?.className).toContain("bg-emerald-50");
    expect(badge?.className).toContain("text-emerald-700");
  });

  it("applies rose classes for offline", () => {
    const { container } = render(<FreshnessBadge status="offline" />);
    const badge = container.querySelector("span");
    expect(badge?.className).toContain("bg-rose-50");
    expect(badge?.className).toContain("text-rose-700");
  });
});
