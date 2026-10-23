import { cn } from "cn";

import { tierLabel } from "@/components/system/labels";

// The swatch of each level; its name comes from labels.ts. A level without one gets an outline.
const SWATCHES: Record<string, string> = {
  local: "bg-tier-local",
  economy: "bg-tier-economy",
  frontier: "bg-tier-frontier",
  cache: "bg-tier-cache",
  denied: "bg-danger",
};

export function TierBadge({ tier, className }: { tier: string; className?: string }) {
  const swatch = Object.hasOwn(SWATCHES, tier) ? SWATCHES[tier] : "border border-ink-3";
  return (
    <span className={cn("inline-flex items-center gap-1.5 whitespace-nowrap font-label text-[13px] font-medium", className)}>
      <span aria-hidden className={cn("size-2.5 shrink-0", swatch)} />
      {tierLabel(tier)}
    </span>
  );
}
