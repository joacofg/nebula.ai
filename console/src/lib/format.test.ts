import { describe, expect, it } from "vitest";

import { formatUsd, formatUsdPer1000 } from "@/lib/format";

describe("formatUsd", () => {
  it("writes USD with two decimals by default, like the thesis", () => {
    expect(formatUsd(0)).toBe("USD 0.00");
    expect(formatUsd(1)).toBe("USD 1.00");
    expect(formatUsd(1.7)).toBe("USD 1.70");
    expect(formatUsd(1696.4)).toBe("USD 1696.40");
  });

  it("uses the digits the call asks for", () => {
    expect(formatUsd(0.0123, 4)).toBe("USD 0.0123");
    expect(formatUsd(0, 4)).toBe("USD 0.0000");
    expect(formatUsd(1.6964, 3)).toBe("USD 1.696");
  });

  it("keeps the sign of a negative amount after USD", () => {
    expect(formatUsd(-0.5)).toBe("USD −0.50");
    expect(formatUsd(-0.1, 4)).toBe("USD −0.1000");
  });

  it("shows no sign when the amount rounds to zero", () => {
    expect(formatUsd(-0.00001, 2)).toBe("USD 0.00");
    expect(formatUsd(-0)).toBe("USD 0.00");
  });

  it("reads a value that is not a number as zero", () => {
    expect(formatUsd(Number.NaN)).toBe("USD 0.00");
    expect(formatUsd(Number.POSITIVE_INFINITY)).toBe("USD 0.00");
  });

  it("never prints a dollar sign", () => {
    expect(formatUsd(12.5)).not.toContain("$");
  });
});

describe("formatUsdPer1000", () => {
  it("scales a per-request cost to 1000 requests", () => {
    expect(formatUsdPer1000(0.0017)).toBe("USD 1.70 / 1000");
    expect(formatUsdPer1000(0)).toBe("USD 0.00 / 1000");
  });

  it("uses the digits the call asks for", () => {
    expect(formatUsdPer1000(0.0016964, 3)).toBe("USD 1.696 / 1000");
  });

  it("reads a value that is not a number as zero", () => {
    expect(formatUsdPer1000(Number.NaN)).toBe("USD 0.00 / 1000");
  });
});
