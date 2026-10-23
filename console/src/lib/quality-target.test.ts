import { describe, expect, it } from "vitest";

import { TARGET_MAX, TARGET_MIN, TARGET_STEP, formatTarget, snapTarget } from "@/lib/quality-target";

describe("quality target range", () => {
  it("is 0.75 to 1.00 on a hundredth grid", () => {
    expect(TARGET_MIN).toBe(0.75);
    expect(TARGET_MAX).toBe(1);
    expect(TARGET_STEP).toBe(0.01);
  });
});

describe("formatTarget", () => {
  it("always shows two decimals", () => {
    expect(formatTarget(0.9)).toBe("0.90");
    expect(formatTarget(0.95)).toBe("0.95");
    expect(formatTarget(0.75)).toBe("0.75");
    expect(formatTarget(1)).toBe("1.00");
  });
});

describe("snapTarget", () => {
  it("clamps to the range", () => {
    expect(snapTarget(0.5)).toBe(0.75);
    expect(snapTarget(0)).toBe(0.75);
    expect(snapTarget(1.2)).toBe(1);
  });

  it("snaps a float to the slider grid", () => {
    expect(snapTarget(0.9123)).toBe(0.91);
    expect(snapTarget(0.9126)).toBe(0.91);
    expect(snapTarget(0.9161)).toBe(0.92);
    expect(snapTarget(0.95)).toBe(0.95);
  });

  it("keeps the ends of the range", () => {
    expect(snapTarget(0.75)).toBe(0.75);
    expect(snapTarget(1)).toBe(1);
  });

  it("only produces targets the two-decimal readout shows exactly", () => {
    for (let raw = 0.7; raw <= 1.05; raw += 0.0013) {
      const snapped = snapTarget(raw);
      expect(Number(formatTarget(snapped))).toBe(snapped);
    }
  });
});
