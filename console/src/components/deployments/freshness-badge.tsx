import type { FreshnessStatus } from "@/lib/admin-api";
import { getFreshnessStyle } from "@/lib/freshness";

type FreshnessBadgeProps = {
  status: FreshnessStatus | null;
};

export function FreshnessBadge({ status }: FreshnessBadgeProps) {
  const { className, label } = getFreshnessStyle(status);
  return (
    <span
      className={[
        "inline-flex items-center rounded-full border px-2 py-1 text-xs font-semibold",
        className,
      ].join(" ")}
    >
      {label}
    </span>
  );
}
