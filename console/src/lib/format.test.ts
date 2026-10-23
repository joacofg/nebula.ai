import { describe, expect, it } from "vitest";

import { formatDateTime, formatUsd, formatUsdPer1000, localInputToIso } from "@/lib/format";

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

describe("formatDateTime", () => {
  it("writes day/month and the time on the viewer's clock", () => {
    // Built from local components so the expectation holds in any time zone.
    expect(formatDateTime(new Date(2026, 9, 22, 14, 5, 3).toISOString())).toBe("22/10 14:05:03");
    expect(formatDateTime(new Date(2026, 0, 3, 9, 0, 7).toISOString())).toBe("03/01 09:00:07");
  });

  it("reads a timestamp without a zone as UTC, the way the gateway stores it", () => {
    // SQLite hands timestamps back without "Z"; reading them as local time would shift the ledger.
    expect(formatDateTime("2026-10-22T14:05:03")).toBe(formatDateTime("2026-10-22T14:05:03Z"));
    expect(formatDateTime("2026-10-22T14:05:03.123456")).toBe(formatDateTime("2026-10-22T14:05:03Z"));
    expect(formatDateTime("2026-10-22T14:05:03+00:00")).toBe(formatDateTime("2026-10-22T14:05:03Z"));
  });

  it("converts an explicit offset instead of ignoring it", () => {
    expect(formatDateTime("2026-10-22T11:05:03-03:00")).toBe(formatDateTime("2026-10-22T14:05:03Z"));
  });

  it("keeps a value that is not a date as written", () => {
    expect(formatDateTime("ayer")).toBe("ayer");
  });
});

describe("localInputToIso", () => {
  it("sends a datetime-local value as the UTC instant the viewer meant", () => {
    expect(localInputToIso("2026-10-22T10:00")).toBe(new Date("2026-10-22T10:00").toISOString());
    expect(localInputToIso("2026-10-22T10:00")).toMatch(/Z$/);
  });

  it("sends nothing for an empty or incomplete value", () => {
    expect(localInputToIso("")).toBe("");
    expect(localInputToIso("2026-10-22T")).toBe("");
  });
});
