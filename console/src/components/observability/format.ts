import { reasonLabel } from "@/components/system/labels";
import { parseTimestamp } from "@/lib/format";

export function formatTimestamp(value: string) {
  const timestamp = parseTimestamp(value);
  if (timestamp === null) {
    return value;
  }
  return timestamp.toLocaleString("es-AR", { dateStyle: "short", timeStyle: "medium", hourCycle: "h23" });
}

/** Reason codes with their counts, in Spanish where the labels know the code and as sent where they do not. */
export function formatReasonCounts(items: Array<{ reason: string; count: number }> | null | undefined) {
  if (!items || items.length === 0) {
    return "ninguna";
  }
  return items.map((item) => `${reasonLabel(item.reason)} (${item.count})`).join(", ");
}
