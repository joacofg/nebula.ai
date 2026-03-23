import type { FreshnessStatus } from "@/lib/admin-api";

const FRESHNESS_STYLES: Record<FreshnessStatus, { className: string; label: string }> = {
  connected: { className: "bg-emerald-50 text-emerald-700 border-emerald-200", label: "Connected" },
  degraded: { className: "bg-amber-50 text-amber-700 border-amber-200", label: "Degraded" },
  stale: { className: "bg-orange-50 text-orange-700 border-orange-200", label: "Stale" },
  offline: { className: "bg-rose-50 text-rose-700 border-rose-200", label: "Offline" },
};

const PENDING_STYLE = {
  className: "bg-amber-50 text-amber-700 border-amber-200",
  label: "Awaiting enrollment",
};

export function getFreshnessStyle(
  status: FreshnessStatus | null,
): { className: string; label: string } {
  if (status === null) return PENDING_STYLE;
  return FRESHNESS_STYLES[status] ?? PENDING_STYLE;
}

const rtf = new Intl.RelativeTimeFormat("en", { numeric: "always" });

export function formatRelativeTime(lastSeenAt: string | null): string {
  if (lastSeenAt === null) return "Never";
  const now = Date.now();
  const seen = new Date(lastSeenAt).getTime();
  const diffMs = now - seen;
  const diffMin = Math.floor(diffMs / 60000);

  if (diffMin < 1) return "Just now";
  if (diffMin < 60) return rtf.format(-diffMin, "minute");
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return rtf.format(-diffHours, "hour");

  // Absolute date for > 24 hours
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(lastSeenAt));
}
