export function titleCaseToken(value: string) {
  return value
    .split(/[_-]/g)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function formatTimestamp(value: string) {
  const timestamp = new Date(value);
  if (Number.isNaN(timestamp.getTime())) {
    return value;
  }
  return timestamp.toLocaleString("es-AR", { dateStyle: "short", timeStyle: "medium" });
}

export function formatReasonCounts(items: Array<{ reason: string; count: number }> | null | undefined) {
  if (!items || items.length === 0) {
    return "ninguna";
  }
  return items.map((item) => `${titleCaseToken(item.reason)} (${item.count})`).join(", ");
}
