/**
 * The one way the console writes money, in the thesis notation: "USD 1.70", point decimal.
 * `digits` is chosen per call (2 for headline figures, 4 for per-request costs). A negative
 * amount keeps its sign after "USD" ("USD −0.50"); one that rounds to zero shows none.
 * A value that is not a finite number reads as zero, so a chart never prints "NaN".
 */
export function formatUsd(value: number, digits = 2): string {
  const amount = Number.isFinite(value) ? value : 0;
  const magnitude = Math.abs(amount).toFixed(digits);
  const isZero = Number(magnitude) === 0;
  return `USD ${amount < 0 && !isZero ? "−" : ""}${magnitude}`;
}

/** A cost per request, scaled to 1000 requests, the unit of the thesis tables: "USD 1.70 / 1000". */
export function formatUsdPer1000(costPerRequest: number, digits = 2): string {
  return `${formatUsd(costPerRequest * 1000, digits)} / 1000`;
}
