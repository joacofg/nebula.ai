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

/**
 * An amount the gateway wrote into a text ("0.1", "unknown"): written like any other amount when it
 * is a number, kept as written after "USD" when it is not.
 */
export function formatUsdText(amount: string, digits = 4): string {
  const value = Number(amount);
  return amount.trim() !== "" && Number.isFinite(value) ? formatUsd(value, digits) : `USD ${amount}`;
}

// A trailing "Z" or UTC offset: the timestamp names its own zone.
const HAS_ZONE = /(?:[zZ]|[+-]\d{2}(?::?\d{2})?)$/;

/**
 * A gateway timestamp as a Date. The gateway stores UTC and SQLite hands the value back without
 * a zone, so one without a zone is UTC, as the backend reads it; JavaScript would take it as local.
 */
export function parseTimestamp(value: string): Date | null {
  const date = new Date(HAS_ZONE.test(value) ? value : `${value}Z`);
  return Number.isNaN(date.getTime()) ? null : date;
}

const two = (n: number) => String(n).padStart(2, "0");

/** A moment on the viewer's clock, short enough for a table cell: "22/10 14:05:03". */
export function formatDateTime(value: string): string {
  const date = parseTimestamp(value);
  if (date === null) {
    return value;
  }
  return `${two(date.getDate())}/${two(date.getMonth() + 1)} ${two(date.getHours())}:${two(date.getMinutes())}:${two(date.getSeconds())}`;
}

const shortDateTime = new Intl.DateTimeFormat("es-AR", { dateStyle: "short", timeStyle: "short", hourCycle: "h23" });

/** A moment on the viewer's clock to the minute, for the tenant and API key tables: "16/3/26, 09:05". */
export function formatDateTimeShort(value: string): string {
  const date = parseTimestamp(value);
  return date === null ? value : shortDateTime.format(date);
}

/**
 * A `datetime-local` value (the viewer's clock, no zone) as the UTC ISO instant the gateway
 * compares against; empty or incomplete input sends nothing.
 */
export function localInputToIso(value: string): string {
  const date = new Date(value);
  return value === "" || Number.isNaN(date.getTime()) ? "" : date.toISOString();
}
